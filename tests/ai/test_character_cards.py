# SPDX-License-Identifier: AGPL-3.0-only
"""Character expansion: shipped content through the normal deck and real compiler."""
import asyncio
from collections import Counter

import pytest

from companion_ai.conversation import character_identity
from companion_ai.event_deck import Eligibility
from tests.ai.test_event_deck_content import (
    ALL, DEFINITION, context, deck, deliver, play_only, prompt, service,
)

PACK = {
    'nova': ('borrowed-wonder', 'alien-menu', 'chosen-name', 'garden-hypothesis',
             'beautiful-error', 'unfamiliar-stars'),
    'daisy': ('rainy-picnic', 'recipe-pride', 'gate-debate', 'welcome-table',
              'friendly-bargain', 'farm-quiet'),
    'evelyn': ('elegant-question', 'imagined-seminar', 'plant-exception', 'null-result',
               'precision-game', 'desk-detour'),
    'celeste': ('defend-detail', 'polished-excuse', 'earned-concession',
                'negotiating-silence', 'revise-position', 'quiet-competence'),
}
MODELS = dict(zip(PACK, ('nova-narrative-f29-v011:latest', 'daisy-narrative-f29-v014:latest',
                        'evelyn-narrative-f29-v013:latest', 'celeste-narrative-f29-v012:latest')))
IDS = {f'{identity}-{suffix}' for identity, suffixes in PACK.items() for suffix in suffixes}
CARDS = [card for card in DEFINITION.normal if card.id in IDS]


def test_expansion_has_six_distinct_prompts_each_and_globally_unique_ids():
    assert len(CARDS) == len(IDS) == 24
    assert len({c.brief for c in CARDS}) == 24
    assert Counter(c.audience for c in CARDS) == {identity: 6 for identity in PACK}
    assert len({c.id for c in ALL}) == len(ALL)


@pytest.mark.parametrize('card', CARDS, ids=lambda c: c.id)
def test_character_cards_need_no_measurements_history_or_memory_permission(card):
    assert card.kind == 'normal' and card.memory == 'none' and card.repeat
    assert card.eligibility == Eligibility(statuses=['RUNNING'])
    target = deck(card.audience)
    assert target._eligible(card, context(signal='missing'))
    for status in ('IDLE', 'PAUSED', 'RAMPDOWN'):
        assert not target._eligible(card, context(status=status))


@pytest.mark.parametrize('identity', [*PACK, 'generic'])
def test_full_shuffle_includes_only_own_pack_once_per_cycle(identity):
    target = deck(identity)
    ctx = context(signal='missing')
    expected = {c.id for c in DEFINITION.normal
                if c.audience in {'shared', identity} and target._eligible(c, ctx)}
    own = {f'{identity}-{suffix}' for suffix in PACK.get(identity, ())}
    assert set(target._queue) & IDS == own
    assert len(target._queue) == len(set(target._queue))
    deliver(target, target.next_play(ctx, 0).play, 0)  # mandatory opening
    cycles = []
    for cycle in range(2):
        drawn = []
        for offset in range(len(expected)):
            now = 1 + cycle * len(expected) + offset
            play = target.next_play(ctx, now).play
            assert play.lane == 'normal'
            assert target.next_play(ctx, now).play is None  # one in-flight delivery
            deliver(target, play, now)
            assert target.transition(play.id, 'delivered', now) is False
            drawn.append(play.card.id)
        assert set(drawn) == expected and len(drawn) == len(set(drawn))
        cycles.append(drawn)
    assert cycles[0][-1] != cycles[1][0]
    assert target.snapshot()['counts']['delivered'] == 1 + 2 * len(expected)


@pytest.mark.parametrize('identity', PACK)
def test_current_f29_model_selects_its_own_expansion(identity):
    assert character_identity(MODELS[identity]) == identity


@pytest.mark.parametrize('card', CARDS, ids=lambda c: c.id)
async def test_expansion_compiles_without_participant_figures_or_story_writes(card):
    r, s, wire, frames = await service(identity=card.audience, edges=5, seconds=900)
    before = list(s.narrative.state['developments'])
    play_only(s, card.id)
    s.pump()
    await s.task
    await asyncio.sleep(0)
    current = prompt(wire)
    assert card.brief in current
    assert 'mention no counts, times or readings' in current
    assert 'Edges this session' not in current and 'Running time:' not in current
    assert s.narrative.state['developments'] == before
    assert len([f for f in frames if f['type'] == 'speech']) == 1
