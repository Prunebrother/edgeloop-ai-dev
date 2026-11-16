# SPDX-License-Identifier: AGPL-3.0-only
"""Reproductions from the Codex review of Chapter 2 (1438df6..a948c59), kept as regression tests."""
import json
import pytest
from ai_observer.server import create_app
from companion_ai.campaign import PLAY_STYLES, PROGRESS_FILE
from companion_ai.settings_control import SettingsControl
from companion_ai.fidelity import violations
from tests.ai.test_campaign import CID, MODEL, run
from tests.ai.test_campaign_chapter2 import seed, tick, frames, view, milestones
from tests.ai.test_settings_control import Adapter
from tests.fork.event_replay import Replay
from tests.fork.test_observer import TOKEN


def control_for(svc):
    control = SettingsControl()
    control.directed = svc.settings_directed()
    control.allowed = svc.allowed_settings()
    control.check = svc.settings_check
    control.still_needed = svc.directive_current
    return control


@pytest.mark.parametrize('campaigns', [[{}], 'broken', 5])
def test_bad_v1_file_disables_campaign_instead_of_crashing_observer(tmp_path, campaigns):
    raw = json.dumps({'schema_version': 1, 'campaigns': campaigns})
    (tmp_path / PROGRESS_FILE).write_text(raw)
    app = create_app(TOKEN, tmp_path)
    assert app.state.campaign.error
    assert (tmp_path / PROGRESS_FILE).read_text() == raw


@pytest.mark.asyncio
async def test_player_switch_during_inference_invalidates_directive(tmp_path):
    svc = seed(tmp_path, 'adaptive_calibration')
    run(svc, 'nova', *frames('n', 0, 300))
    [directive] = svc.take_directives()
    before = tick('n', 300)
    after = tick('n', 305, style='milker')
    sent = []
    class SlowDecision:
        async def decide_settings(self, *args):
            run(svc, 'nova', after)
            assert not svc.directive_valid(directive, after)
            return '{"change":"none"}'
    await control_for(svc).run(SlowDecision(), before, MODEL['nova'], sent.append, directive=directive)
    assert sent == [], 'The player already chose a valid new style while inference ran'


@pytest.mark.asyncio
async def test_game_off_directive_cannot_be_replaced_by_style_switch(tmp_path):
    svc = seed(tmp_path, 'adaptive_calibration')
    report = tick('n', 0, goal='survival')
    run(svc, 'nova', report)
    [directive] = svc.take_directives()
    assert directive['fallback']['setting'] == 'game'
    request = await control_for(svc).run(
        Adapter('{"change":"play_style","value":"finisher","reason":"Try this."}'),
        report, MODEL['nova'], lambda message: None, directive=directive)
    assert request['setting'] == 'game' and request['value'] == 'off'


def test_reconnect_first_frame_does_not_credit_unobserved_interval(tmp_path):
    svc = seed(tmp_path, 'adaptive_calibration')
    replay = Replay()
    replay.state['devices'].update(hr_ready=True, ble=True, simulated_hr=False, toy_ready=True, handy=True)
    replay.state['safety'].update(signal='ok', fault='none')
    replay.step(90, seconds=0)
    svc.observe(replay.observation.report, [], MODEL['nova'])
    replay.step(90, seconds=1)
    svc.observe(replay.observation.report, [], MODEL['nova'])
    assert svc.attempt.style_time['classic'] == 1
    replay.observation.begin_epoch()
    replay.clock.tick(100)
    replay.step(90, seconds=1)
    svc.observe(replay.observation.report, [], MODEL['nova'])
    assert svc.attempt.style_time['classic'] == 1


def test_partial_styles_cannot_report_more_than_full_mission_progress(tmp_path):
    svc = seed(tmp_path, 'adaptive_calibration')
    for index, style in enumerate(PLAY_STYLES):
        run(svc, 'nova', *frames('n', index * 305, index * 305 + 295, style=style))
    objective = view(svc, 'styles')
    assert objective['progress'] == 0
    assert objective['elapsed'] <= objective['count'] * objective['stage_seconds']


@pytest.mark.asyncio
async def test_verified_assessment_time_is_not_checked_as_whole_session_time(tmp_path):
    from tests.ai.test_event_deck_content import service as speech
    from companion_ai.settings_control import CARD_KIND
    r, s, wire, outputs = await speech(identity='celeste', seconds=2410,
        reply='Thirty minutes of active assessment time, and now you can finish.')
    svc = seed(tmp_path, 'directors_reassessment')
    sid = s.state.session_id
    run(svc, 'celeste', *frames(sid, 0, 600, intensity=75))
    run(svc, 'celeste', *frames(sid, 605, 1200, intensity=75))
    run(svc, 'celeste', *frames(sid, 1205, 1805, intensity=100))
    run(svc, 'celeste', *frames(sid, 1810, 2410, intensity=125))
    assert view(svc, 'assessment')['elapsed'] == 1800
    assert view(svc, 'assessment')['done']
    s.campaign_brief = lambda: svc.model_context(MODEL['celeste'], r.observation.report)
    base = s.adapter.current_summary
    s.adapter.current_summary = lambda: base() | s.campaign_fields()
    event = {'kind': CARD_KIND, 'session_id': sid, 'source_status': 'RUNNING', 'deck_card': {
        'lane': 'normal', 'memory': 'none', 'card_id': CARD_KIND, 'speaker': 'celeste',
        'brief': 'React to your verified change: Force Orgasm is now on for the assessment finish.',
        'settings_change': {'setting': 'orgasm', 'from': False, 'to': True, 'reason': 'The assessment is complete.'}}}
    assert s.request('Observed application event (not a user request): Force Orgasm switched on for the mission finish.',
        user=False, event=event)['accepted']
    await s.task
    assert [m for m in outputs if m['type'] == 'speech'], s.adapter.grounding_corrections


def test_count_jump_to_completion_does_not_lose_crossed_milestones(tmp_path):
    svc = seed(tmp_path, 'endurance_study')
    run(svc, 'evelyn', tick('e', 0))
    out = run(svc, 'evelyn', tick('e', 1, edges=15))
    assert milestones(out) == ['edges:5', 'edges:10']


def test_crossed_milestones_wait_for_a_failed_completion_save(tmp_path):
    svc = seed(tmp_path, 'endurance_study')
    run(svc, 'evelyn', tick('e', 0))
    write = svc.store.write
    def broken(*args): raise OSError('disk full')
    svc.store.write = broken
    assert milestones(run(svc, 'evelyn', tick('e', 1, edges=15))) == []
    svc.store.write = write
    out = run(svc, 'evelyn', tick('e', 2, edges=15))
    assert milestones(out) == ['edges:5', 'edges:10'] and out[-1]['type'] == 'mission_result'


# ---- Retest (Codex, 7d59581)

def test_mission_clock_never_validates_a_session_clock_claim(tmp_path):
    from tests.ai.test_campaign_chapter2 import tick as t
    svc = seed(tmp_path, 'directors_reassessment')
    replay = Replay()
    sid = replay.state['session_id']
    run(svc, 'celeste', *frames(sid, 0, 1200, intensity=75))
    replay.state.update(seconds=1200, intensity=75)
    replay.step(None, seconds=0)
    canonical = replay.observation.summary()['canonical_session']
    durations = svc.model_context(MODEL['celeste'], replay.observation.report)['durations']
    assert 600 in durations
    assert 'wrong_running_counter' in violations('The session clock shows ten minutes.', canonical, card=True, durations=durations)
    assert 'wrong_running_counter' not in violations('Ten minutes of the baseline stage are done.', canonical, card=True, durations=durations)


def test_a_client_without_capture_times_gets_no_mission_time(tmp_path):
    svc = seed(tmp_path, 'adaptive_calibration')
    frames_ = frames('n', 0, 20)
    for f in frames_: f['details'].pop('captured_at_ms')
    run(svc, 'nova', *frames_)
    assert svc.attempt.style_time.get('classic', 0) == 0


@pytest.mark.parametrize('failed_save', [False, True])
def test_crossed_milestones_come_before_the_cleared_state(tmp_path, failed_save):
    svc = seed(tmp_path, 'endurance_study')
    run(svc, 'evelyn', tick('e', 0))
    write = svc.store.write
    if failed_save:
        def broken(*args): raise OSError('disk full')
        svc.store.write = broken
        run(svc, 'evelyn', tick('e', 1, edges=15))
        svc.store.write = write
    out = run(svc, 'evelyn', tick('e', 2, edges=15))
    assert [m['type'] for m in out] == ['mission_milestone', 'mission_milestone', 'campaign_state', 'mission_result']
