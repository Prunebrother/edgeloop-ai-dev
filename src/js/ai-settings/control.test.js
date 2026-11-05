// SPDX-License-Identifier: AGPL-3.0-only
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createAiSettingsControl } from './control.js';

function harness({ settings = { enabled: true }, refuse = false } = {}) {
    let clock = 1000000;
    const engine = { status: 'RUNNING', signal: 'ok', toyReady: true,
        current: { play_style: 'classic', game: 'off', endgame: 'orgasm', orgasm: false, intensity: 50 } };
    const applied = [];
    let saved = null;
    const control = createAiSettingsControl({
        load: () => settings, save: (value) => { saved = value; }, now: () => clock,
        context: () => ({ status: engine.status, signal: engine.signal, toyReady: engine.toyReady, current: { ...engine.current } }),
        apply: (change) => {
            applied.push(change);
            if (refuse) return;
            if (change.setting === 'pause') engine.status = 'PAUSED';
            else if (change.setting === 'stop') engine.status = 'IDLE';
            else engine.current[change.setting] = change.to;
        }
    });
    const ask = (setting, value, id = 'req_' + String(applied.length + 10).padStart(8, '0')) =>
        control.request({ version: 1, type: 'settings_request', id, session_id: 's1', setting, value, reason: 'You looked too relaxed.' }, { sessionId: 's1' });
    return { control, engine, applied, ask, tick: (ms) => { clock += ms; }, saved: () => saved };
}

test('off by default: nothing is applied until the user enables it', () => {
    const h = harness({ settings: null });
    assert.equal(h.control.settings().enabled, false);
    assert.equal(h.ask('play_style', 'bratty').reason, 'disabled');
    assert.equal(h.applied.length, 0);
    h.control.configure({ enabled: true });
    assert.deepEqual(h.saved(), { ...h.control.settings() });
    assert.equal(h.ask('play_style', 'bratty').status, 'applied');
});

test('auto mode applies, reports from/to and the reason, and advances the snapshot counter', () => {
    const h = harness();
    const result = h.ask('endgame', 'denial');
    assert.deepEqual([result.status, result.from, result.to, result.reason, result.undoable], ['applied', 'orgasm', 'denial', 'You looked too relaxed.', true]);
    assert.deepEqual(h.control.snapshot(), { enabled: true, revoked: false, applied: 1, last_id: result.id, last_setting: 'endgame', applying_id: null });
});

test('a change the engine silently refuses is reported as rejected, not applied', () => {
    const h = harness({ refuse: true });
    const result = h.ask('game', 'oracle');
    assert.deepEqual([result.status, result.reason], ['rejected', 'engine_refused']);
    assert.equal(h.control.snapshot().applied, 0);
});

test('rate limit counts from the last applied change', () => {
    const h = harness();
    assert.equal(h.ask('intensity', 60).status, 'applied');
    assert.equal(h.ask('play_style', 'milker').reason, 'rate_limited');
    h.tick(45000);
    assert.equal(h.ask('play_style', 'milker').status, 'applied');
});

test('emergency stop revokes until the user starts a new session', () => {
    const h = harness();
    h.control.revoke();
    assert.equal(h.ask('pause', true).reason, 'revoked_by_emergency_stop');
    assert.equal(h.control.snapshot().revoked, true);
    h.control.newSession();
    assert.equal(h.ask('pause', true).status, 'applied');
});

test('Undo restores the previous value once, only while the AI value is still current', () => {
    const h = harness();
    const result = h.ask('play_style', 'bratty');
    assert.equal(h.control.undo(result.id), true);
    assert.equal(h.engine.current.play_style, 'classic');
    assert.equal(h.control.undo(result.id), false);
    h.tick(45000);
    const second = h.ask('intensity', 70);
    h.engine.current.intensity = 40;
    assert.equal(h.control.undo(second.id), false);
    assert.equal(h.engine.current.intensity, 40);
    assert.equal(h.ask('pause', true).undoable, false);
});

test('ask mode waits for the user and re-checks the request on confirm', () => {
    const h = harness({ settings: { enabled: true, mode: 'ask' } });
    const pending = h.ask('orgasm', true, 'req_aaaaaaaa');
    assert.equal(pending.status, 'pending');
    assert.equal(h.applied.length, 0);
    assert.equal(h.ask('intensity', 60).reason, 'confirmation_pending');
    assert.equal(h.ask('pause', true).status, 'applied', 'pause never waits for confirmation');
    assert.equal(h.control.confirm('req_aaaaaaaa').reason, 'not_running', 'the session moved on, so the request is refused');
    h.engine.status = 'RUNNING';
    h.ask('endgame', 'denial', 'req_bbbbbbbb');
    assert.equal(h.control.decline('req_bbbbbbbb').reason, 'declined_by_user');
    h.ask('endgame', 'denial', 'req_cccccccc');
    assert.equal(h.control.confirm('req_cccccccc').status, 'applied');
});

test('the audit log is bounded and records rejections', () => {
    const h = harness();
    for (let i = 0; i < 70; i += 1) h.ask('SESSION_RESET', true);
    const audit = h.control.audit();
    assert.equal(audit.length, 50);
    assert.ok(audit.every((entry) => entry.status === 'rejected' && entry.reason === 'invalid_request'));
});

test('the projection taken during an AI change is labelled; a user Undo is not', () => {
    const seen = [];
    let control;
    const current = { play_style: 'classic', game: 'off', endgame: 'orgasm', orgasm: false, intensity: 50 };
    control = createAiSettingsControl({ load: () => ({ enabled: true }), now: () => 0,
        context: () => ({ status: 'RUNNING', signal: 'ok', toyReady: true, current: { ...current } }),
        apply: (change) => { current[change.setting] = change.to; seen.push(control.snapshot().applying_id); } });
    const result = control.request({ version: 1, type: 'settings_request', id: 'req_labelled', session_id: 's', setting: 'play_style', value: 'ruin' }, { sessionId: 's' });
    assert.equal(control.snapshot().applying_id, null);
    control.undo(result.id);
    assert.deepEqual(seen, ['req_labelled', null]);
});
