# SPDX-License-Identifier: AGPL-3.0-only
"""Evelyn's arrival, 2026-11-16: the facts said 27 edges and 1 reported orgasm; she greeted
the player with "a single edge and a solitary climax". The figures are now dealt on separate
lines, and "single/lone/solitary edge" is checked as the count 1, like "one edge" already was."""
import pytest
from companion_ai.context_compiler import arrival_facts
from companion_ai.fidelity import history_violations, spoken_number

HISTORY = {'status': 'found', 'since_seconds': 6 * 86400 + 3600,
           'prior': {'edges': 27, 'seconds': 1400, 'experience': 'headplay', 'goal': 'tease',
                     'outcome': 'user_reported', 'comparable': True, 'orgasms': 1}}
SUMMARY = {'deck_card': {'lane': 'arrival', 'history': HISTORY}}


def test_edges_length_and_orgasms_are_separate_lines_that_cannot_be_swapped():
    lines = arrival_facts(HISTORY)
    assert 'Edges in the previous session: 27.' in lines
    assert 'Length of the previous session: 23 minutes 20 seconds.' in lines
    assert 'Orgasms the participant reported in it: 1. That is the orgasm count; the edge count is the 27 above.' in lines
    assert not any('27 edges in' in line for line in lines)


def test_unknown_figures_stay_explicit():
    lines = arrival_facts({**HISTORY, 'prior': {**HISTORY['prior'], 'seconds': None}})
    assert 'Length of the previous session: not known, so say nothing about how long it ran.' in lines
    lines = arrival_facts({**HISTORY, 'prior': {**HISTORY['prior'], 'edges': None, 'seconds': None}})
    assert lines[1] == 'The previous session: edge count and length not known, so state neither.'


def test_no_orgasm_note_when_the_counts_match():
    lines = arrival_facts({**HISTORY, 'prior': {**HISTORY['prior'], 'edges': 1}})
    assert 'Orgasms the participant reported in it: 1.' in lines


@pytest.mark.parametrize('word', ['single', 'singular', 'lone', 'solitary', 'sole'])
def test_one_without_a_number_word_is_one(word):
    assert spoken_number(word) == 1


@pytest.mark.parametrize('reply', [
    'You finished with a single edge and a solitary climax; I find that efficiency both refreshing and slightly underwhelming.',
    'Your last run was efficient, a single edge delivered with the precision of a surgeon.',
    'Your last effort left us with a single, rather modest edge to celebrate.',
    'You claimed that singular edge for yourself.',
    'That single, solitary edge was underwhelming.',
    'You finished with a lone edge.',
])
def test_a_single_edge_contradicting_the_record_is_caught(reply):
    assert 'unsupported_history_figure' in history_violations(reply, SUMMARY)


@pytest.mark.parametrize('reply', [
    'Twenty-seven edges in a single session is a formidable tally.',
    'Twenty-seven edges to fuel a single climax; quite the ratio.',
    'That single reported climax still lingers in my notes.',
    'You walked a single knife edge between restraint and release.',
    'A single razor-sharp edge of wit.',
])
def test_single_about_something_else_is_not_an_edge_count(reply):
    assert 'unsupported_history_figure' not in history_violations(reply, SUMMARY)
