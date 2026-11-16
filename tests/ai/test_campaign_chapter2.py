# SPDX-License-Identifier: AGPL-3.0-only
"""Chapter 2 of the Asterion Initiative (docs/fork/campaign/README.md): chapters, milestones, active-time stages,
the staged assessment, save migration and replay. Evidence is the engine's canonical report only."""
import json
import pytest
from companion_ai.campaign import Book, Campaign, PROGRESS_FILE, SCHEMA_VERSION
from tests.ai.test_campaign import CID, CHAPTER2, MODEL, ORDER, brief, report, results, run, service, states

STAMP = '2026-11-16T00:00:00+00:00'


def seed(tmp_path, mission=None, version=SCHEMA_VERSION):
    """Saved progress with every mission before `mission` completed (all missions when None)."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    campaign = Book.load().campaign(CID)
    record = {'missions': {}, 'rewards': {}, 'completed_at': None, 'records': {}}
    for m in sorted(campaign.missions, key=lambda m: m.order):
        if m.id == mission: break
        record['missions'][m.id] = {'completions': 1, 'first_completed_at': STAMP, 'last_completed_at': STAMP}
        for r in m.rewards: record['rewards'][r.key] = {'earned_at': STAMP, 'mission': m.id}
    if version >= 2: record['chapters'] = {}
    (tmp_path / PROGRESS_FILE).write_text(json.dumps({'schema_version': version, 'campaigns': {CID: record}, 'active': None}))
    svc = service(tmp_path)
    if mission: svc.start(CID, mission)
    return svc


def tick(sid, seconds, style='classic', intensity=100, status='RUNNING', goal='tease', **extra):
    r = report(sid=sid, status=status, **extra)
    r.update(seconds=seconds, experience=style, intensity=intensity, goal=goal)
    return r


def frames(sid, start, end, step=5, **kw):
    return [tick(sid, t, **kw) for t in range(start, end + 1, step)]


def milestones(out):
    return [m['key'] for m in out if m['type'] == 'mission_milestone']


def view(svc, oid, r=None):
    return next(o for o in svc.state(r)['attempt']['objectives'] if o['id'] == oid)


# ---- chapters and unlocking

def test_chapters_are_listed_with_their_missions(tmp_path):
    campaign = service(tmp_path).state()['campaigns'][0]
    assert [(c['number'], c['id'], c['title']) for c in campaign['chapters']] == [(1, 'introduction', 'Introduction'), (2, 'advanced_research', 'Advanced Research')]
    assert [m['chapter'] for m in campaign['missions']] == [1] * 5 + [2] * 4
    assert campaign['chapters'][0]['available'] and not campaign['chapters'][1]['available']
    # New text is marked as a draft; Chapter 1's approved narrative is not.
    assert [m['narrative_draft'] for m in campaign['missions']] == [False] * 5 + [True] * 4


def test_chapter_two_opens_after_mission_five_and_unlocks_in_order(tmp_path):
    svc = seed(tmp_path, 'certification')
    assert states(svc)['endurance_study'] == 'locked'
    run(svc, 'nova', report(sid='c', mode='calibrate', calibration_pass='primary', single_max_bpm=150))
    out = svc.observe(report(sid='c', status='IDLE', mode='calibrate', orgasms=1, calibration_pass='primary', single_max_bpm=150,
                             calibration_saved=True, terminal_outcome='calibration_completed'), ['completion_accepted'], MODEL['nova'])
    [result] = results(out)
    assert result['unlocked_missions'] == ['endurance_study'] and result['chapter_complete']['id'] == 'introduction'
    assert [states(svc)[m] for m in CHAPTER2] == ['available', 'locked', 'locked', 'locked']
    chapters = svc.state()['campaigns'][0]['chapters']
    assert chapters[0]['completed'] and chapters[1]['available'] and chapters[1]['progress'] == {'completed': 0, 'total': 4}
    for i, mission in enumerate(CHAPTER2[1:], 1):
        with pytest.raises(ValueError, match='locked'): svc.start(CID, mission)
        seed(tmp_path / str(i), mission)  # every earlier mission done: this one is the next to open
        assert states(service(tmp_path / str(i)))[mission] == 'active'


@pytest.mark.parametrize('mission,companion', zip(CHAPTER2, ['evelyn', 'daisy', 'nova', 'celeste']))
def test_each_mission_counts_only_with_its_companion(tmp_path, mission, companion):
    svc = seed(tmp_path, mission)
    other = 'nova' if companion != 'nova' else 'daisy'
    run(svc, other, report(sid='x'))
    assert svc.state()['attempt']['session_id'] is None
    run(svc, companion, report(sid='x'))
    assert svc.state()['attempt']['session_id'] == 'x'


# ---- Mission 6: fifteen edges, milestones at 5 and 10

def test_endurance_study_marks_five_and_ten_once_and_completes_at_fifteen(tmp_path):
    svc = seed(tmp_path, 'endurance_study')
    out = run(svc, 'evelyn', report(sid='e'))
    assert milestones(out) == ['start']
    assert milestones(run(svc, 'evelyn', report(sid='e', edges=4))) == []
    assert milestones(run(svc, 'evelyn', report(sid='e', edges=5), report(sid='e', edges=5))) == ['edges:5']
    assert milestones(run(svc, 'evelyn', report(sid='e', edges=12))) == ['edges:10']  # a jump past a threshold marks it once
    out = run(svc, 'evelyn', report(sid='e', edges=15))
    [result] = results(out)
    assert milestones(out) == [] and result['records']['endurance_study.edges'] == 15
    assert result['unlocked_missions'] == ['cloverfield_quota']


def test_endurance_edges_with_another_companion_or_the_simulator_do_not_count(tmp_path):
    svc = seed(tmp_path, 'endurance_study')
    run(svc, 'evelyn', report(sid='e'), report(sid='e', edges=3))
    run(svc, 'nova', report(sid='e', edges=8))
    run(svc, 'evelyn', report(sid='e', edges=10, sim=True))
    run(svc, 'evelyn', report(sid='e', edges=11))
    assert view(svc, 'edges')['progress'] == 4


def test_a_milestone_is_shown_again_only_in_a_new_try(tmp_path):
    svc = seed(tmp_path, 'endurance_study')
    run(svc, 'evelyn', report(sid='a'), report(sid='a', edges=5))
    run(svc, 'evelyn', report(sid='a', status='IDLE', edges=5))
    assert view(svc, 'edges')['progress'] == 0
    assert milestones(run(svc, 'evelyn', report(sid='b'), report(sid='b', edges=5))) == ['start', 'edges:5']


# ---- Mission 7: two reported orgasms in one session

def test_cloverfield_quota_needs_two_separate_reports(tmp_path):
    svc = seed(tmp_path, 'cloverfield_quota')
    run(svc, 'daisy', report(sid='q'))
    out = run(svc, 'daisy', report(sid='q', orgasms=1), report(sid='q', orgasms=1), report(sid='q', status='PAUSED', orgasms=1),
              report(sid='q', orgasms=1, completion_reported=True))
    assert milestones(out) == ['orgasms:1'] and not results(out) and view(svc, 'orgasms')['progress'] == 1
    [result] = results(run(svc, 'daisy', report(sid='q', orgasms=2)))
    assert result['records']['cloverfield_quota.orgasms'] == 2


def test_came_early_can_be_the_second_report(tmp_path):
    svc = seed(tmp_path, 'cloverfield_quota')
    run(svc, 'daisy', report(sid='q'), report(sid='q', orgasms=1))
    assert results(svc.observe(report(sid='q', status='IDLE', orgasms=1, terminal_outcome='premature_release'), ['came_early'], MODEL['daisy']))


def test_one_report_then_the_session_ends_starts_again(tmp_path):
    svc = seed(tmp_path, 'cloverfield_quota')
    run(svc, 'daisy', report(sid='q'), report(sid='q', orgasms=1), report(sid='q', status='IDLE', orgasms=1))
    run(svc, 'daisy', report(sid='r'), report(sid='r', orgasms=1))
    assert view(svc, 'orgasms')['progress'] == 1 and states(svc)['cloverfield_quota'] == 'active'


# ---- Mission 8: four play styles, five minutes of active time each

def test_four_styles_of_five_minutes_complete_adaptive_calibration(tmp_path):
    svc = seed(tmp_path, 'adaptive_calibration')
    out = []
    for i, style in enumerate(['classic', 'milker', 'headplay', 'ultimate']):
        out += run(svc, 'nova', *frames('n', 400 * i, 400 * i + 300, style=style))
    [result] = results(out)
    assert milestones(out) == ['start', 'styles:1', 'styles:2', 'styles:3']
    assert result['records']['adaptive_calibration.styles'] == 'Simple Ramp, Prostate Milker, Head Play, Ultimate Milker'
    assert result['unlocked_missions'] == ['directors_reassessment']


def test_one_style_fills_only_one_stage(tmp_path):
    svc = seed(tmp_path, 'adaptive_calibration')
    run(svc, 'nova', *frames('n', 0, 1500, style='classic'))
    v = view(svc, 'styles')
    assert v['progress'] == 1 and not v['done'] and v['elapsed'] == 300


def test_pauses_games_style_changes_and_gaps_do_not_count(tmp_path):
    svc = seed(tmp_path, 'adaptive_calibration')
    run(svc, 'nova', *frames('n', 0, 100, style='milker'))                     # 100 s
    run(svc, 'nova', tick('n', 100, style='milker', status='PAUSED'), tick('n', 100, style='milker', status='PAUSED'))
    run(svc, 'nova', *frames('n', 100, 150, style='milker'))                   # +50 s; the resume interval is 0 s
    run(svc, 'nova', tick('n', 154, style='headplay'))                         # the change interval counts for nothing
    run(svc, 'nova', tick('n', 158, style='milker'))                           # nor the change back
    run(svc, 'nova', *frames('n', 158, 168, style='milker', goal='survival'))  # a game is on
    run(svc, 'nova', tick('n', 200, style='milker'))                           # a 32 s gap is unknown time
    run(svc, 'nova', tick('n', 205, style='milker', sim=True))                 # the simulator never counts
    run(svc, 'nova', tick('n', 210, style='milker'))
    assert svc.attempt.style_time == {'milker': 150}
    stage = view(svc, 'styles', tick('n', 210, style='milker'))['stages'][0]
    assert stage == {'style': 'milker', 'label': 'Prostate Milker', 'seconds': 150, 'done': False, 'current': True}


def test_the_brief_tells_nova_the_stage_clock(tmp_path):
    svc = seed(tmp_path, 'adaptive_calibration')
    run(svc, 'nova', *frames('n', 0, 300, style='classic'), *frames('n', 305, 365, style='ruin'))
    text = brief(svc, 'nova', tick('n', 365, style='ruin'))['text']
    assert '1 of 4 play-style stages complete (Simple Ramp)' in text and 'current play style Ruin & Leak: 1:00 of 5:00' in text
    assert 'already filled a stage' in brief(svc, 'nova', tick('n', 366, style='classic'))['text']


# ---- Mission 9: the 30-minute staged assessment, then the finish

def assessment(svc, sid='d'):
    """Each stage starts with the frame that changes the intensity (that interval counts for nothing), then 600 s."""
    out = []
    for i, level in enumerate([75, 100, 125]):
        out += run(svc, 'celeste', *frames(sid, 605 * i, 605 * i + 600, intensity=level))
    return out


def test_the_reassessment_runs_three_stages_then_needs_the_finish(tmp_path):
    svc = seed(tmp_path, 'directors_reassessment')
    assert svc.allowed_settings() == {'intensity'}
    out = assessment(svc)
    assert milestones(out) == ['start', 'assessment:development', 'assessment:final', 'assessment:done']
    assert not results(out) and view(svc, 'assessment')['done'] and view(svc, 'assessment')['elapsed'] == 1800
    # The final phase allows Force Orgasm through AI Settings Control; the scripted line replaces the model card.
    assert svc.allowed_settings() == {'intensity', 'orgasm'}
    assert not [c for c in svc.take_cues() if c['kind'] == 'objective_reached']
    [result] = results(run(svc, 'celeste', tick('d', 1815, intensity=125, orgasms=1)))
    assert result['chapter_complete']['id'] == 'advanced_research' and result['campaign_complete']
    assert result['chapter_completion']['status'] == 'draft'
    campaign = svc.state()['campaigns'][0]
    assert campaign['completed'] and all(c['completed'] for c in campaign['chapters'])


def test_an_orgasm_before_the_final_phase_does_not_count(tmp_path):
    svc = seed(tmp_path, 'directors_reassessment')
    run(svc, 'celeste', *frames('d', 0, 600, intensity=75))
    run(svc, 'celeste', tick('d', 605, intensity=75, orgasms=1))
    assert view(svc, 'finish')['progress'] == 0
    out = run(svc, 'celeste', *frames('d', 605, 1200, intensity=100, orgasms=1), *frames('d', 1205, 1800, intensity=125, orgasms=1))
    assert not results(out) and view(svc, 'finish')['progress'] == 0


def test_the_wrong_intensity_pauses_the_stage_clock(tmp_path):
    svc = seed(tmp_path, 'directors_reassessment')
    run(svc, 'celeste', *frames('d', 0, 300, intensity=75))
    run(svc, 'celeste', *frames('d', 305, 400, intensity=100))  # too high for the baseline: nothing counts
    run(svc, 'celeste', *frames('d', 405, 500, intensity=77))   # within 2%: counts again
    stages = view(svc, 'assessment')['stages']
    assert stages[0]['elapsed'] == 395 and stages[0]['current'] and not stages[0]['done']
    text = brief(svc, 'celeste', tick('d', 501, intensity=60))['text']
    assert 'stage 1 of 3, "Baseline", at 75% intensity: 6:35 of 10:00' in text and 'paused until the participant sets 75%' in text


@pytest.mark.parametrize('stop_at,outcome', [(300, 'manual_stop'), (900, 'safety_stop'), (1500, 'manual_stop'), (1800, 'safety_stop')])
def test_stopping_in_any_stage_ends_the_try_and_the_next_session_starts_from_zero(tmp_path, stop_at, outcome):
    svc = seed(tmp_path, 'directors_reassessment')
    levels = lambda t: 75 if t <= 600 else 100 if t <= 1200 else 125
    run(svc, 'celeste', *[tick('d', t, intensity=levels(t)) for t in range(0, stop_at + 1, 5)])
    out = run(svc, 'celeste', tick('d', stop_at, status='IDLE', intensity=levels(stop_at), terminal_outcome=outcome))
    assert not results(out) and svc.state()['attempt']['reset_reason'] == 'session_ended'
    assert view(svc, 'assessment')['elapsed'] == 0 and svc.allowed_settings() == {'intensity'}
    assert states(svc)['directors_reassessment'] == 'active'


def test_celeste_is_told_only_what_the_saved_reports_show(tmp_path):
    svc = seed(tmp_path, 'directors_reassessment')
    text = brief(svc, 'celeste', report(sid='d', status='IDLE'))['text']
    # Missions completed under earlier versions keep no figures, so she gets completion only.
    assert 'Mission 6 "The Endurance Study" (evelyn): completed, with no further detail on record' in text
    progress = json.loads((tmp_path / PROGRESS_FILE).read_text())
    progress['campaigns'][CID]['records'].update({'endurance_study.edges': 15, 'adaptive_calibration.styles': 'Simple Ramp, Head Play'})
    (tmp_path / PROGRESS_FILE).write_text(json.dumps(progress))
    text = brief(service(tmp_path), 'celeste', report(sid='d', status='IDLE'))['text']
    assert 'completed with 15 edges' in text and 'play styles Simple Ramp, Head Play' in text


# ---- rewards, replay and saved progress

def test_a_replay_grants_nothing_twice_and_keeps_the_chapter(tmp_path):
    svc = seed(tmp_path)
    svc.start(CID, 'endurance_study')
    run(svc, 'evelyn', report(sid='r'))
    [result] = results(run(svc, 'evelyn', report(sid='r', edges=15)))
    assert result['replay'] and result['earned'] == [] and result['chapter_complete'] is None
    saved = json.loads((tmp_path / PROGRESS_FILE).read_text())['campaigns'][CID]
    assert saved['missions']['endurance_study']['completions'] == 2 and saved['chapters']['advanced_research']['completed_at'] == STAMP


def test_version_1_progress_becomes_chapter_1_complete(tmp_path):
    """A version 1 file that finished the old five-mission campaign keeps everything, Chapter 2 opens,
    and the campaign is no longer complete."""
    record = {'missions': {m: {'completions': 1, 'first_completed_at': STAMP, 'last_completed_at': STAMP} for m in ORDER},
              'rewards': {'unlock_companion:evelyn': {'earned_at': STAMP, 'mission': 'orientation'},
                          'campaign_complete:asterion_initiative': {'earned_at': STAMP, 'mission': 'certification'}},
              'completed_at': STAMP, 'records': {'calibrated_max_bpm': 150}}
    (tmp_path / PROGRESS_FILE).write_text(json.dumps({'schema_version': 1, 'campaigns': {CID: record}, 'active': None}))
    svc = service(tmp_path)
    campaign = svc.state()['campaigns'][0]
    assert svc.error is None and not campaign['completed'] and campaign['records']['calibrated_max_bpm'] == 150
    assert [m['state'] for m in campaign['missions']] == ['completed'] * 5 + ['available', 'locked', 'locked', 'locked']
    assert campaign['chapters'][0]['completed'] and campaign['chapters'][0]['completed_at'] == STAMP
    svc.start(CID, 'endurance_study')
    saved = json.loads((tmp_path / PROGRESS_FILE).read_text())
    assert saved['schema_version'] == 2 and saved['campaigns'][CID]['completed_at'] is None
    assert set(saved['campaigns'][CID]['rewards']) == {'unlock_companion:evelyn', 'chapter_complete:introduction'}


def test_a_malformed_chapter_2_record_leaves_the_file_and_freeplay_alone(tmp_path):
    seed(tmp_path)
    progress = json.loads((tmp_path / PROGRESS_FILE).read_text())
    progress['campaigns'][CID]['missions']['adaptive_calibration'] = {'completions': 0}
    raw = json.dumps(progress)
    (tmp_path / PROGRESS_FILE).write_text(raw)
    svc = service(tmp_path)
    assert svc.error and svc.observe(report(), [], MODEL['nova']) == [] and svc.allowed_settings() is None
    with pytest.raises(ValueError): svc.start(CID, 'orientation')
    assert (tmp_path / PROGRESS_FILE).read_text() == raw


def test_progress_of_a_removed_mission_is_ignored(tmp_path):
    seed(tmp_path)
    progress = json.loads((tmp_path / PROGRESS_FILE).read_text())
    progress['campaigns'][CID]['missions']['old_mission'] = {'completions': 1, 'first_completed_at': STAMP, 'last_completed_at': STAMP}
    (tmp_path / PROGRESS_FILE).write_text(json.dumps(progress))
    svc = service(tmp_path)
    assert svc.error is None and svc.state()['campaigns'][0]['progress'] == {'completed': 9, 'total': 9}


# ---- definitions

def definition(objective):
    return {'schema_version': 1, 'id': 'x', 'order': 1, 'title': 'x', 'description': 'x', 'starting_companions': ['nova'],
            'missions': [{'id': 'm', 'order': 1, 'title': 'M', 'summary': 'x', 'companion': 'nova', 'objectives': [objective]}]}


@pytest.mark.parametrize('objective', [
    {'id': 'e', 'type': 'edge_count', 'count': 5, 'milestones': [5], 'label': 'x'},            # a milestone at the target
    {'id': 'e', 'type': 'edge_count', 'count': 5, 'milestones': [3, 2], 'label': 'x'},         # not increasing
    {'id': 's', 'type': 'style_stages', 'count': 4, 'label': 'x'},                             # no seconds
    {'id': 's', 'type': 'style_stages', 'count': 3, 'seconds': 60, 'styles': ['classic', 'ruin'], 'label': 'x'},
    {'id': 'q', 'type': 'stage_sequence', 'label': 'x'},                                       # no stages
    {'id': 'q', 'type': 'stage_sequence', 'label': 'x', 'stages': [{'id': 'a', 'label': 'A', 'seconds': 60, 'intensity': 75},
                                                                   {'id': 'a', 'label': 'B', 'seconds': 60, 'intensity': 100}]},
    {'id': 'o', 'type': 'orgasm_count', 'count': 1, 'after': 'o', 'label': 'x'},               # after itself
])
def test_bad_objective_definitions_are_rejected(objective):
    with pytest.raises(ValueError):
        Campaign.model_validate(definition(objective))
