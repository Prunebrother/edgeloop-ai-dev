# SPDX-License-Identifier: AGPL-3.0-only
"""Campaign progression (docs/fork/campaign/README.md): definitions, verified objectives, rewards, saved progress."""
import json
from pathlib import Path
import pytest
from companion_ai.campaign import Book, CampaignService, Campaign, PROGRESS_FILE, real_hr
from companion_ai.settings_control import SettingsControl
from companion_ai.storage import SettingsStore

MODELS = {'nova-narrative-f29-v011:latest': 'nova', 'evelyn-narrative-f29-v013:latest': 'evelyn',
          'daisy-narrative-f29-v014:latest': 'daisy', 'celeste-narrative-f29-v012:latest': 'celeste',
          'mira-narrative-f29-v015:latest': 'mira'}
MODEL = {v: k for k, v in MODELS.items()}
ORDER = ['orientation', 'first_assessment', 'country_connections', 'directors_test', 'certification']
CID = 'asterion_initiative'


def identity(model):
    return MODELS.get(model)


def service(tmp_path, book=None):
    return CampaignService(SettingsStore(tmp_path), book=book, identity=identity)


def report(status='RUNNING', sid='s1', edges=0, orgasms=0, hr=True, ble=True, sim=False, toy=True, mode='classic', **extra):
    details = {'orgasm_count': orgasms, 'calibration_pass': 'none'} | extra
    return {'session_id': sid, 'status': status, 'edges': edges, 'active_mode': mode, 'goal': 'tease',
            'devices': {'hr_ready': hr, 'ble': ble, 'simulated_hr': sim, 'toy_ready': toy},
            'details': details}


def states(svc):
    campaign = svc.state()['campaigns'][0]
    return {m['id']: m['state'] for m in campaign['missions']}


def run(svc, companion, *reports, events=()):
    out = []
    for r in reports:
        out += svc.observe(r, list(events), MODEL[companion])
    return out


def results(out):
    return [m for m in out if m['type'] == 'mission_result']


def finish_orientation(svc):
    svc.start(CID, 'orientation')
    return results(run(svc, 'nova', report(edges=0), report(edges=1)))


# ---- 4. registration and discovery

def test_the_shipped_campaign_loads_and_is_available_from_the_start(tmp_path):
    book = Book.load()
    assert book.errors == []
    assert [c.id for c in book.campaigns] == [CID]
    state = service(tmp_path).state()
    campaign = state['campaigns'][0]
    assert campaign['title'] == 'The Asterion Initiative' and campaign['available'] and not campaign['completed']
    assert [m['id'] for m in campaign['missions']] == ORDER
    assert [m['companion'] for m in campaign['missions']] == ['nova', 'evelyn', 'daisy', 'celeste', 'nova']
    assert campaign['progress'] == {'completed': 0, 'total': 5}
    assert campaign['narrative_status'] == 'approved'
    assert all(m['briefing'] for m in campaign['missions'])


def test_a_second_campaign_registers_from_data_alone(tmp_path):
    root = tmp_path / 'campaigns'
    for cid, order in (('second_story', 2), ('first_story', 1)):
        (root / cid).mkdir(parents=True)
        (root / cid / 'campaign.json').write_text(json.dumps({'schema_version': 1, 'id': cid, 'order': order, 'title': cid,
            'description': 'x', 'starting_companions': ['nova'], 'missions': [{'id': 'one', 'order': 1, 'title': 'One', 'summary': 'x',
            'companion': 'nova', 'objectives': [{'id': 'e', 'type': 'edge_count', 'count': 1, 'label': 'Edge'}]}]}))
    book = Book.load(root)
    assert [c.id for c in book.campaigns] == ['first_story', 'second_story'] and book.errors == []


@pytest.mark.parametrize('change,error', [
    (lambda c: c['missions'][1].update(prerequisites=['nope']), 'unknown prerequisite'),
    (lambda c: c['missions'][0].update(prerequisites=['certification']), 'cycle'),
    (lambda c: c['missions'][1].update(companion='mira'), 'never unlocked'),
    (lambda c: c['missions'][0]['objectives'].append({'id': 'x', 'type': 'edge_count', 'label': 'x'}), 'count is required'),
    (lambda c: c['missions'][0]['objectives'].append({'id': 'x', 'type': 'llm_said_so', 'label': 'x'}), 'Input should be'),
])
def test_invalid_definitions_are_rejected(change, error):
    data = json.loads((Path(__file__).resolve().parents[2] / 'config/campaigns' / CID / 'campaign.json').read_text())
    change(data)
    with pytest.raises(ValueError, match=error):
        Campaign.model_validate(data)


def test_a_broken_campaign_is_skipped_and_the_others_still_load(tmp_path):
    root = tmp_path / 'campaigns'
    (root / 'broken').mkdir(parents=True)
    (root / 'broken' / 'campaign.json').write_text('{not json')
    book = Book.load(root)
    assert book.campaigns == [] and book.errors[0]['path'] == 'broken'


# ---- 5. prerequisites and companion unlocks

def test_only_the_first_mission_is_available_at_the_start(tmp_path):
    assert states(service(tmp_path)) == {'orientation': 'available', 'first_assessment': 'locked', 'country_connections': 'locked',
                                         'directors_test': 'locked', 'certification': 'locked'}
    with pytest.raises(ValueError, match='locked'):
        service(tmp_path).start(CID, 'first_assessment')


def test_a_mission_cannot_start_during_a_running_session(tmp_path):
    with pytest.raises(ValueError, match='Stop the current session'):
        service(tmp_path).start(CID, 'orientation', report(status='PAUSED'))


# ---- 6, 7, 8. completion, successor unlock, companion reward

def test_orientation_completes_on_one_real_edge_and_unlocks_evelyn(tmp_path):
    svc = service(tmp_path)
    svc.start(CID, 'orientation')
    assert states(svc)['orientation'] == 'active'
    out = run(svc, 'nova', report(edges=0))
    attempt = out[0]['attempt']
    assert {o['id']: o['done'] for o in attempt['objectives']} == {'hr': True, 'toy': True, 'start': True, 'edge': False}
    out = run(svc, 'nova', report(edges=1))
    [result] = results(out)
    assert result['mission'] == 'orientation' and not result['replay']
    assert result['earned'] == [{'type': 'unlock_companion', 'id': 'evelyn', 'label': 'Dr. Evelyn Voss joins the campaign'}]
    assert result['unlocked_missions'] == ['first_assessment']
    assert result['completion']['speaker'] == 'nova'
    assert states(svc)['orientation'] == 'completed' and states(svc)['first_assessment'] == 'available'
    assert svc.state()['campaigns'][0]['companions'] == ['evelyn', 'nova']


def test_the_session_keeps_running_after_completion_and_the_result_is_sent_once(tmp_path):
    svc = service(tmp_path)
    assert len(finish_orientation(svc)) == 1
    assert run(svc, 'nova', report(edges=2), report(edges=3), report(status='IDLE', edges=3)) == []


def test_nothing_counts_before_hr_toy_and_companion_are_in_place(tmp_path):
    svc = service(tmp_path)
    svc.start(CID, 'orientation')
    assert results(run(svc, 'nova', report(edges=0, hr=False), report(edges=1, hr=False))) == []
    assert results(run(svc, 'nova', report(sid='s2', edges=0, sim=True), report(sid='s2', edges=1, sim=True))) == []
    assert results(run(svc, 'nova', report(sid='s3', edges=0, toy=False), report(sid='s3', edges=1, toy=False))) == []
    assert results(run(svc, 'evelyn', report(sid='s4', edges=0), report(sid='s4', edges=1))) == []
    assert results(run(svc, 'nova', report(sid='s5', edges=0), report(sid='s5', edges=1)))


def test_the_heart_rate_simulator_is_not_a_monitor():
    assert real_hr(report()) and not real_hr(report(sim=True)) and not real_hr(report(ble=False))


def test_edges_made_with_another_companion_selected_do_not_count(tmp_path):
    svc = service(tmp_path)
    finish_orientation(svc)
    svc.start(CID, 'first_assessment')
    run(svc, 'evelyn', report(sid='a', edges=0), report(sid='a', edges=2))
    run(svc, 'nova', report(sid='a', edges=6))
    assert svc.state()['attempt']['objectives'][3]['progress'] == 2
    assert results(run(svc, 'evelyn', report(sid='a', edges=9)))


def test_five_edges_must_fall_in_one_session(tmp_path):
    svc = service(tmp_path)
    finish_orientation(svc)
    svc.start(CID, 'first_assessment')
    out = run(svc, 'evelyn', report(sid='a', edges=0), report(sid='a', edges=4), report(sid='a', status='IDLE', edges=4))
    assert results(out) == [] and svc.state()['attempt']['reset_reason'] == 'session_ended'
    assert svc.state()['attempt']['objectives'][3]['progress'] == 0
    assert results(run(svc, 'evelyn', report(sid='b', edges=0), report(sid='b', edges=5)))[0]['earned'][0]['id'] == 'daisy'


@pytest.mark.parametrize('final', [
    {'orgasms': 1},                                   # I came
    {'completion_reported': True},                    # Survival's Finished me
])
def test_an_orgasm_reported_through_the_engine_counts_once(tmp_path, final):
    svc = _to(tmp_path, 'country_connections')
    out = run(svc, 'daisy', report(sid='c'), report(sid='c', **{('orgasms' if 'orgasms' in final else 'completion_reported'): list(final.values())[0]}))
    assert results(out)[0]['earned'][0]['id'] == 'celeste'


def test_came_early_counts_as_an_orgasm(tmp_path):
    svc = _to(tmp_path, 'country_connections')
    run(svc, 'daisy', report(sid='c'))
    assert results(svc.observe(report(sid='c', status='IDLE'), ['came_early', 'stop'], MODEL['daisy']))


def test_an_orgasm_and_completion_report_together_count_one(tmp_path):
    svc = _to(tmp_path, 'directors_test')
    run(svc, 'celeste', report(sid='d'), report(sid='d', edges=5, orgasms=1, completion_reported=True))
    # 5 edges + 1 orgasm finished it; the second orgasm objective never needed a second report.
    assert states(svc)['directors_test'] == 'completed'


def test_directors_test_needs_both_counts_in_one_session(tmp_path):
    svc = _to(tmp_path, 'directors_test')
    assert results(run(svc, 'celeste', report(sid='d'), report(sid='d', orgasms=1), report(sid='d', status='IDLE', orgasms=1))) == []
    assert results(run(svc, 'celeste', report(sid='e'), report(sid='e', edges=5))) == []
    [result] = results(run(svc, 'celeste', report(sid='e', edges=5, orgasms=1)))
    assert result['unlocked_missions'] == ['certification'] and result['earned'][0]['id'] == 'assessments_passed'


# ---- Mission 5: Calibration ending with Finished me

def calibrate(**extra):
    return report(mode='calibrate', calibration_pass='primary', single_max_bpm=150, **extra)


def test_certification_needs_calibration_mode(tmp_path):
    svc = _to(tmp_path, 'certification')
    run(svc, 'nova', report(sid='f'))
    assert svc.state()['attempt']['session_id'] is None


def test_certification_completes_the_campaign_on_a_saved_finished_me_run(tmp_path):
    svc = _to(tmp_path, 'certification')
    run(svc, 'nova', calibrate(sid='f'), calibrate(sid='f', orgasms=1, calibration_saved=True))
    [result] = results(svc.observe(calibrate(sid='f', status='IDLE', orgasms=1, calibration_saved=True, terminal_outcome='calibration_completed'),
                                   ['completion_accepted'], MODEL['nova']))
    assert result['campaign_complete'] and result['campaign_completion']['speaker'] == 'nova'
    assert result['records'] == {'calibration_pass': 'primary', 'calibrated_max_bpm': 150}
    state = service(tmp_path).state()['campaigns'][0]
    assert state['completed'] and state['progress'] == {'completed': 5, 'total': 5}


def test_edged_saves_the_max_but_does_not_certify(tmp_path):
    svc = _to(tmp_path, 'certification')
    run(svc, 'nova', calibrate(sid='f'), calibrate(sid='f', edges=1, calibration_saved=True))
    out = svc.observe(calibrate(sid='f', status='IDLE', edges=1, calibration_saved=True, terminal_outcome='calibration_completed'), ['completion_accepted'], MODEL['nova'])
    assert results(out) == [] and states(svc)['certification'] == 'active'


def test_a_failed_save_does_not_certify(tmp_path):
    svc = _to(tmp_path, 'certification')
    run(svc, 'nova', calibrate(sid='f'), calibrate(sid='f', orgasms=1, calibration_saved=False))
    out = svc.observe(calibrate(sid='f', status='IDLE', orgasms=1, calibration_saved=False, terminal_outcome='calibration_completed'), ['completion_accepted'], MODEL['nova'])
    assert results(out) == [] and not svc.state()['campaigns'][0]['completed']


def test_ai_settings_are_limited_to_intensity_during_certification_only(tmp_path):
    svc = _to(tmp_path, 'certification')
    assert svc.allowed_settings() == frozenset({'intensity'})
    svc.abandon()
    assert svc.allowed_settings() is None
    svc.start(CID, 'orientation')
    assert svc.allowed_settings() is None


def test_settings_control_drops_a_restricted_request():
    import asyncio

    class Adapter:
        def __init__(self, answer): self.answer = answer
        async def decide_settings(self, content, schema, timeout):
            self.content = content
            return json.dumps(self.answer)
    ai = {'enabled': True, 'revoked': False, 'applied': 0, 'own_ready': True}
    r = report(mode='calibrate') | {'intensity': 100, 'experience': 'classic', 'seconds': 60}
    r['details'] |= {'ai_settings': ai, 'endgame': 'orgasm', 'orgasm_mode': False}
    control = SettingsControl(); control.allowed = frozenset({'intensity'}); sent = []
    adapter = Adapter({'change': 'game', 'value': 'survival', 'reason': 'x'})
    assert asyncio.run(control.run(adapter, r, 'm', sent.append)) is None and sent == []
    assert control.diagnostics['status'] == 'restricted' and 'only these changes are possible: intensity' in adapter.content
    assert asyncio.run(control.run(Adapter({'change': 'intensity', 'value': 70, 'reason': 'x'}), r, 'm', sent.append))['setting'] == 'intensity'


# ---- 9, 10, 12. persistence, duplicates, replay

def test_progress_survives_a_restart(tmp_path):
    svc = service(tmp_path)
    finish_orientation(svc)
    svc.start(CID, 'first_assessment')
    again = service(tmp_path)
    assert states(again)['orientation'] == 'completed' and states(again)['first_assessment'] == 'active'
    assert again.attempt and again.attempt.session_id is None  # a session never resumes across restarts
    saved = json.loads((tmp_path / PROGRESS_FILE).read_text())
    assert saved['schema_version'] == 1 and saved['active']['mission'] == 'first_assessment'
    assert set(saved['campaigns'][CID]['rewards']) == {'unlock_companion:evelyn'}


def test_replay_grants_nothing_twice(tmp_path):
    svc = service(tmp_path)
    finish_orientation(svc)
    svc.start(CID, 'orientation')
    [again] = results(run(svc, 'nova', report(sid='y'), report(sid='y', edges=1)))
    assert again['replay'] and again['earned'] == [] and again['unlocked_missions'] == []
    saved = json.loads((tmp_path / PROGRESS_FILE).read_text())['campaigns'][CID]
    assert saved['missions']['orientation']['completions'] == 2 and list(saved['rewards']) == ['unlock_companion:evelyn']


def test_a_failed_save_announces_nothing_and_retries(tmp_path):
    svc = service(tmp_path)
    svc.start(CID, 'orientation')
    real = svc.store.write
    svc.store.write = lambda *a: (_ for _ in ()).throw(OSError('disk full'))
    out = run(svc, 'nova', report(edges=0), report(edges=1))
    assert results(out) == [] and 'could not be saved' in svc.state()['notice']
    svc.store.write = real
    assert results(run(svc, 'nova', report(edges=1)))
    assert states(service(tmp_path))['orientation'] == 'completed'


# ---- 11. invalid or missing data

def test_no_file_means_a_fresh_start(tmp_path):
    assert service(tmp_path).error is None and not (tmp_path / PROGRESS_FILE).exists()


@pytest.mark.parametrize('content', ['{broken', '[]', '{"schema_version": 1, "campaigns": {"asterion_initiative": {"missions": {"orientation": {"completions": "lots"}}}}}',
                                     '{"schema_version": 99}', '{"schema_version": true}'])
def test_unreadable_progress_is_kept_and_disables_only_the_campaign(tmp_path, content):
    (tmp_path / PROGRESS_FILE).write_text(content)
    svc = service(tmp_path)
    assert svc.error and svc.state()['error']
    with pytest.raises(ValueError):
        svc.start(CID, 'orientation')
    assert svc.observe(report(edges=3), [], MODEL['nova']) == []
    assert (tmp_path / PROGRESS_FILE).read_text() == content


def test_progress_for_removed_content_is_ignored(tmp_path):
    (tmp_path / PROGRESS_FILE).write_text(json.dumps({'schema_version': 1, 'active': {'campaign': 'gone', 'mission': 'x', 'started_at': 't'},
        'campaigns': {'gone': {'missions': {'x': {'completions': 1, 'first_completed_at': 't', 'last_completed_at': 't'}}}}}))
    svc = service(tmp_path)
    assert svc.error is None and svc.attempt is None and states(svc)['orientation'] == 'available'


# ---- 13. campaign isolation

def test_progress_is_kept_per_campaign(tmp_path):
    root = tmp_path / 'campaigns'
    for cid in ('alpha', 'beta'):
        (root / cid).mkdir(parents=True)
        (root / cid / 'campaign.json').write_text(json.dumps({'schema_version': 1, 'id': cid, 'order': 1, 'title': cid, 'description': 'x',
            'starting_companions': ['nova'], 'missions': [{'id': 'one', 'order': 1, 'title': 'One', 'summary': 'x', 'companion': 'nova',
            'objectives': [{'id': 'e', 'type': 'edge_count', 'count': 1, 'label': 'Edge'}],
            'rewards': [{'type': 'unlock_companion', 'id': 'evelyn', 'label': 'Evelyn'}]}]}))
    svc = service(tmp_path / 'data', Book.load(root))
    svc.start('alpha', 'one')
    results(run(svc, 'nova', report(edges=0), report(edges=1)))
    by_id = {c['id']: c for c in svc.state()['campaigns']}
    assert by_id['alpha']['completed'] is False and by_id['alpha']['progress']['completed'] == 1
    assert by_id['beta']['progress']['completed'] == 0 and by_id['beta']['companions'] == ['nova']
    assert by_id['beta']['missions'][0]['state'] == 'available' and by_id['beta']['missions'][0]['rewards'][0]['earned'] is False


def test_abandon_clears_the_active_mission_and_keeps_completions(tmp_path):
    svc = service(tmp_path)
    finish_orientation(svc)
    svc.start(CID, 'first_assessment')
    svc.abandon()
    again = service(tmp_path)
    assert again.progress.active is None and states(again)['orientation'] == 'completed' and states(again)['first_assessment'] == 'available'


def _to(tmp_path, mission):
    """Progress saved as if every mission before `mission` was completed, then `mission` started."""
    svc = service(tmp_path)
    for done in ORDER[:ORDER.index(mission)]:
        svc.start(CID, done)
        companion = svc.attempt.mission.companion
        if done == 'certification':
            raise AssertionError('not needed')
        sid = 'pre-' + done
        if done == 'country_connections':
            out = run(svc, companion, report(sid=sid), report(sid=sid, orgasms=1))
        elif done == 'directors_test':
            out = run(svc, companion, report(sid=sid), report(sid=sid, edges=5, orgasms=1))
        else:
            out = run(svc, companion, report(sid=sid), report(sid=sid, edges=5))
        assert results(out), done
    svc.start(CID, mission)
    return svc


# ---- Through the observer: the browser can navigate, only accepted engine evidence completes

def test_observer_websocket_runs_a_mission_end_to_end(tmp_path):
    import time
    from uuid import uuid4
    from fastapi.testclient import TestClient
    from ai_observer.server import create_app
    from tests.fork.test_observer import TOKEN, ORIGIN, auth, until, frame, snapshot
    app = create_app(TOKEN, tmp_path)
    app.state.models.config = app.state.models.config.model_copy(update={'model': 'nova-narrative-f29-v011:latest'})
    sid = str(uuid4())

    def state(**updates):
        s = snapshot()
        s.update({'session_id': sid, 'edges': 0} | updates)
        s['devices'] |= {'simulated_hr': False, 'ble': True, 'hr_ready': True, 'toy_ready': True, 'handy': True}
        s['details'] = {'captured_at_ms': int(time.time() * 1000), 'hr_recorded_at_ms': None, 'calibration_pass': 'none', 'warmup_active': False,
                        'resting_bpm': 70, 'single_max_bpm': 150, 'dual_max_bpm': None, 'pauses': 0, 'warmup_remaining_seconds': None,
                        'ease_down_seconds': None, 'rampdown_seconds': None}
        return s
    with TestClient(app) as client:
        with client.websocket_connect('/observe', headers={'Origin': ORIGIN}) as ws:
            ready = auth(ws)
            ws.send_json({'version': 1, 'type': 'campaign', 'action': 'get'})
            assert until(ws, 'campaign_state')['campaigns'][0]['missions'][0]['state'] == 'available'
            ws.send_json({'version': 1, 'type': 'campaign', 'action': 'start', 'campaign_id': CID, 'mission_id': 'first_assessment'})
            assert 'locked' in until(ws, 'campaign_state')['command_error']
            ws.send_json({'version': 1, 'type': 'campaign', 'action': 'start', 'campaign_id': CID, 'mission_id': 'orientation'})
            assert until(ws, 'campaign_state')['active']['mission'] == 'orientation'
            ws.send_json(frame(ready['epoch'], seq=1, state=state(status='IDLE', seconds=0, hr=None)))
            assert until(ws, 'observation_ack')['accepted']
            time.sleep(.12)
            ws.send_json(frame(ready['epoch'], seq=2, state=state(seconds=1, hr=None)))
            # The campaign update is published before the observation is acknowledged.
            assert until(ws, 'campaign_state', 3)['attempt']['session_id'] == sid
            assert until(ws, 'observation_ack', 3)['accepted']
            time.sleep(.12)
            ws.send_json(frame(ready['epoch'], seq=3, state=state(seconds=5, edges=1, hr=None)))
            result = until(ws, 'mission_result')
            assert result['mission'] == 'orientation' and result['earned'][0]['id'] == 'evelyn'
    saved = json.loads((tmp_path / PROGRESS_FILE).read_text())
    assert saved['active'] is None and 'orientation' in saved['campaigns'][CID]['missions']
