"""Several orgasms in one session: I came counts one, the session keeps running, the companion
reacts each time and knows how many there were this session and across its recorded sessions."""
from copy import deepcopy
import json
import pytest
from companion_ai.context_compiler import PHASE_FACTS, orgasm_facts
from companion_ai.event_deck import RECOVERY_SECONDS, session_phase
from companion_ai.session_history import earlier_orgasms
from companion_ai.settings_control import ROUND_REST_SECONDS, Proposal, decision_content, proposal_request
from tests.ai.test_event_deck_content import DEFINITION, context, deck, play_only, prompt, service
from tests.ai.test_f251 import change
from tests.ai.test_f284 import SCOPE, setup, stop


def running(seconds=300, count=1, last=280, orgasm_mode=False):
    return {'session_id': 's', 'status': 'RUNNING', 'seconds': seconds, 'experience': 'classic', 'goal': 'tease', 'intensity': 100,
            'details': {'orgasm_mode': orgasm_mode, 'orgasm_count': count, 'last_orgasm_seconds': last, 'endgame': 'orgasm'}}


# Phase

@pytest.mark.parametrize('seconds,phase', [(280, 'recovery'), (280 + RECOVERY_SECONDS - 1, 'recovery'), (280 + RECOVERY_SECONDS, 'building')])
def test_recovery_lasts_the_window_after_a_reported_orgasm(seconds, phase):
    assert session_phase(running(seconds)) == phase


def test_a_new_force_orgasm_during_recovery_is_a_finish_again():
    assert session_phase(running(300, orgasm_mode=True)) == 'finishing'


# Observer and journal

def report_orgasm(c, o, s, count, seconds):
    s = deepcopy(s); s['details'].update(orgasm_count=count, last_orgasm_seconds=seconds)
    return change(c, o, s, 'orgasm_reported', seconds=seconds)


def test_each_reported_orgasm_is_an_accepted_event_and_the_journal_keeps_the_count(tmp_path):
    c, o, s, j = setup(tmp_path)
    s, accepted = report_orgasm(c, o, s, 1, 240)
    assert accepted and o.report['status'] == 'RUNNING'
    assert any(e['kind'] == 'orgasm_reported' and 'session count 0 -> 1' in e['evidence'] for e in o.events)
    s, accepted = report_orgasm(c, o, s, 2, 520)
    assert accepted and sum(e['kind'] == 'orgasm_reported' for e in o.events) == 2
    s = stop(c, o, s)
    record = j.data['records'][0]
    assert record['orgasms'] == 2 and record['completion_status'] == 'user_reported'
    assert o.completed_sessions[-1]['orgasms'] == 2
    assert j.snapshot(sort='orgasms')['records'][0]['orgasms'] == 2
    assert j.retrieve('How many edges did the previous session have?', SCOPE)[0]['orgasms'] == 2


def test_an_unchanged_count_proves_no_orgasm(tmp_path):
    c, o, s, j = setup(tmp_path)
    s, _ = change(c, o, s, 'orgasm_reported', seconds=60)
    assert not any(e['kind'] == 'orgasm_reported' for e in o.events)


class Journal:
    def __init__(self, records, access=True):
        self.error = None
        self.data = {'ai_access': access, 'records': records}


def row(session, orgasms, scope=SCOPE):
    return {'session_id': session, 'orgasms': orgasms, 'companions': [{'model_scope': scope, 'companion': 'evelyn'}]}


def test_the_all_time_total_counts_only_this_companions_own_sessions_and_needs_permission():
    journal = Journal([row('a', 2), row('b', 1), row('c', 5, 'other-scope'), row('now', 9)])
    assert earlier_orgasms(journal, SCOPE, {'now'}) == 3
    assert earlier_orgasms(Journal([row('a', 2)], access=False), SCOPE) is None


# Card prompt facts

@pytest.mark.parametrize('card,lane,result,expected,absent', [
    ({'intent': 'orgasm_reaction', 'orgasms': 2, 'total_orgasms': 7, 'total_known': True}, 'mission', None,
     ['this session: 2', 'this one included: 7'], []),
    ({'intent': 'general_conversation', 'orgasms': 1, 'total_orgasms': 4, 'total_known': True}, 'normal', None,
     ['this session: 1'], ['all your recorded sessions']),
    ({'intent': 'general_conversation', 'orgasms': 0, 'total_orgasms': 4, 'total_known': True}, 'normal', None, [], ['Orgasms']),
    ({'intent': 'orgasm_total', 'orgasms': 0, 'total_orgasms': 0, 'total_known': False}, 'normal', None,
     ['this session: 0', 'not available to you'], ['all your recorded sessions']),
    ({'intent': 'session_closing', 'orgasms': 0, 'total_orgasms': 3, 'total_known': True}, 'session_end', {'orgasms': 2},
     ['this session: 2', 'this one included: 5'], []),
    ({'intent': 'arrival_returning', 'orgasms': 0, 'total_orgasms': 6, 'total_known': True}, 'arrival', None,
     ['all your recorded sessions together: 6'], ['this session', 'this one included']),
])
def test_orgasm_counts_reach_only_the_cards_that_need_them(card, lane, result, expected, absent):
    text = '\n'.join(orgasm_facts(card, lane, result))
    assert all(e in text for e in expected) and not any(a in text for a in absent), text


async def test_a_recovery_card_is_told_the_session_goes_on_and_the_count():
    r, s, wire, _ = await service(seconds=300, orgasms=1, last_orgasm=290)
    play_only(s, 'recovery-still-going')
    s.pump(); await s.task
    current = prompt(wire)
    assert PHASE_FACTS['recovery'] in current and 'Orgasms the participant reported this session: 1.' in current


async def test_the_orgasm_reaction_plays_again_for_every_reported_orgasm():
    r, s, wire, frames = await service(seconds=300, orgasms=1, last_orgasm=290)
    target = s.deck(); target._start_done = True; target._queue = []; target._played = []
    for n in (1, 2):
        target.verified_event('orgasm_reported', f'orgasm-{n}', target.session_id, n)
        s.pump(); await s.task
        assert 'The participant just reported an orgasm' in prompt(wire)
        assert 'Verified result' not in prompt(wire)
    assert [a['sequence_id'] for a in target._activations].count('orgasm-reported') == 2


def test_one_reaction_at_a_time_for_quick_successive_reports():
    target = deck('nova')
    assert target.verified_event('orgasm_reported', 'one', target.session_id, 1) == ['orgasm-reported']
    assert target.verified_event('orgasm_reported', 'two', target.session_id, 2) == []


# AI Settings Control

def test_the_decision_step_knows_the_count_and_the_rest_rule():
    content = decision_content(running(300, 2, 200))
    assert 'Orgasms the participant reported this session: 2, the last one 1 min 40 s ago' in content
    assert 'never within 3 minutes of the last orgasm' in content


@pytest.mark.parametrize('trigger,since,allowed', [('own', ROUND_REST_SECONDS - 1, False), ('own', ROUND_REST_SECONDS, True), ('user', 10, True)])
def test_an_own_new_round_waits_for_the_rest_but_a_user_request_does_not(trigger, since, allowed):
    proposal = Proposal.model_validate({'change': 'orgasm', 'value': True, 'reason': 'Another one.'})
    assert (proposal_request(proposal, running(300 + since, 1, 300), trigger) is not None) is allowed
