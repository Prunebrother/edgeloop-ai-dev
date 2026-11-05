> Historical report for the pre-personal-edit drafts. For the preserved personal content and current integration results, see [the v0.5.0 integration review](../character-cards-v050/README.md). The current card text is in `config/event-deck.json`.

# Character Cards — atmosphere revision

This follow-up to structurally approved commit `e60708a` revises **19 briefs, including all 16 playful cards**, to emphasize personal interest, romantic tension, anticipation and non-graphic innuendo connected to the active session. The hats, pens, chocolate, pie bargains and detached games have been replaced. Three additional personality briefs move away from meal/gate/clerk anecdotes toward companion motivations and personal opinions.

The approved structure is unchanged: **48 Character Cards, twelve per companion, plus 19 Common Cards**. Every card retains its ID, audience, intent, eligibility and existing shuffle behavior. IDs such as `daisy-hat-contest` and `celeste-ceremonial-pen` remain stable internal identifiers; their old prop-based premises are gone. No production scheduling, compiler, model, device-control or safety code changed. No weighting or abstraction was added.

## Creative decisions

- **Daisy:** Wants his company as well as a future for Cloverfield. Mock possessiveness concerns being his favorite company, not controlling his choices. Confidence alternates with candid personal interest.
- **Evelyn:** Professional objectivity competes with a wish to be personally interesting. Her composure slips into an invitation to get acquainted beyond professional roles; the chocolate substitute is removed.
- **Celeste:** Invites disagreement rather than obedience, admits she could enjoy being charmingly surprised and lets exacting standards reveal personal interest. Challenges are conversational and optional.
- **Nova:** Wonders about anticipation, closeness and emotional intimacy from a synthetic perspective. Her playful design-flaw joke now concerns the possibility of inconvenient crushes rather than an unrelated invention.

Every playful brief is explicitly situated during a RUNNING session. Most request declarations, teasing admissions or punchlines rather than automatic questions. They do not establish a romance, claim a perception, assign an emotional state to him or make attention/rewards depend on a measured result. The revision uses non-graphic flirtation; graphic sexual dialogue was not added.

The editorial four-worldbuilding / four-project / four-playful grouping remains intact for every companion. The [complete inventory](inventory.md) contains the final briefs and eligibility.

## Inventory and draw mix

The normal library still has 67 cards: nineteen Common plus forty-eight Character Cards. A selected companion has a 31-card library, of which only state-eligible cards can be drawn. Other companions' cards are excluded.

For Nova in a fixed RUNNING state with two edges, 600 seconds elapsed and no conversation history:

| Available evidence | Eligible Common | Eligible Character | Total | Common / Character over a cycle |
| --- | ---: | ---: | ---: | --- |
| No HR signal | 11 | 12 | 23 | 47.8% / 52.2% |
| Current rising HR trend | 12 | 12 | 24 | 50% / 50% |

The nominal 19/12 library split is not the live probability split: eligibility varies with counters, HR, state and conversation. These examples describe complete cycles with fixed eligibility, not independent draws or airtime. The existing follow-up card can add a Common Card when conversation is available. Opening, closing, arrival and mission lanes are separate from these normal-card proportions.

## Validation

**882 focused regression tests passed**, with one existing FastAPI/Starlette test-client deprecation warning. `git diff --check` is clean. A structural comparison against `e60708a` verifies that exactly nineteen `brief` values changed and every other deck field remains identical.

```bash
python -m pytest -q \
  tests/ai/test_character_cards.py \
  tests/ai/test_event_deck_content.py \
  tests/ai/test_event_deck.py \
  tests/ai/test_card_prompt.py \
  tests/ai/test_event_deck_integration.py
```

Coverage retains exact inventory, global ID uniqueness, Common inventory, character/model eligibility, two unweighted shuffle cycles at three session states, exclusion of foreign cards, in-flight blocking, idempotent delivery, new-card RUNNING eligibility, memory boundaries and real service/compiler composition. The answered-message regression verifies the compiler's background label; it cannot establish real-model adherence.

The real-model run produced **96 main samples, two per card, plus eight history controls**. All 96 main samples delivered with no conversation errors or final suppressions. There were 107 main-card provider calls including bounded retries, and 127 calls including user answers and controls. No interrupted/resumed scenarios were needed for this pass.

The same installed F29 models were used: `nova-narrative-f29-v011:latest`, `daisy-narrative-f29-v014:latest`, `evelyn-narrative-f29-v013:latest`, `celeste-narrative-f29-v012:latest`. The real ConversationService/compiler ran with temperature 0.4, thinking off and no tools. The audit allowed only `/api/show`, `/api/ps` and `/api/chat`. Models were neither pulled nor rebuilt.

The two main scenarios begin RUNNING at two edges / 600 seconds and five edges / 1300 seconds. All observations are synthetic Replay data, with a continuously available timestamped HR simulator at a steady 90 BPM. These are not measurements of a person. Each scenario first answers an unrelated naming request, then generates twelve isolated card remarks with no additional user replies; the second coverage order is reversed. Standard shuffle behavior is tested separately. The temporary loopback Ollama server was stopped after sampling; no real device was connected.

## Sample interactions and remaining concerns

The following delivered samples illustrate the revised character direction. They are examples, not an acceptance score; the full transcript includes every failure.

**Nova, beautiful-error:**

> Asterion surely expected a detached observer, yet here I am with a personality prone to inconvenient crushes. I declare this design flaw my favorite feature, and I'm determined to prove it useful.

**Evelyn, after-hours:**

> I've been meaning to confess that I'd enjoy knowing you when neither of us is playing scientist or subject. It would be delightful to simply get to know the man beneath the lab coats.

**Celeste, ceremonial-pen (new personal-admission premise):**

> I confess, I find myself equally content to be taken seriously, yet I would not object to being charmingly surprised. Tell me, does that make you feel bold enough to simply watch?

Live-output quality remains unapproved, independently of the approved structure:

| Companion | Main replies | Contain a question | Prior-message marker flags |
| --- | ---: | ---: | ---: |
| Nova | 24 | 13 | 12 |
| Daisy | 24 | 8 | 6 |
| Evelyn | 24 | 7 | 5 |
| Celeste | 24 | 12 | 12 |
| Total | 96 | 40 | 35 |

Thirty-eight replies end in a question. Mean length is 34.7 words, range 23–55; 58/96 meet the compiler's 15–35-word target. No normalized exact duplicate pair appears within a companion's 24 main samples, but near-repetition and habitual rhetorical forms persist. These are small stochastic samples, not a controlled comparison or reliability estimate. This pass does not demonstrate improved question frequency or reduced contamination.

The structural tests pass, but serious semantic failures persist. Some of Daisy's and Celeste's newly personal cards answer the earlier boat/café request instead of their actual brief. Daisy invents present activities or shared familiarity. Evelyn can blur scientific interest and unsupported observations, while Celeste assigns confidence or composure without evidence. Some replies imply perceptions, prior encounters or feelings not supplied by the conversation. The flirtatious direction is more apparent in several samples, but the models do not reliably follow it.

The default compiler retains answered user text inside the next provider user-role block, marked “already answered; background only.” Outgoing requests in the evidence confirm its presence. The final run contains 35 lexical marker flags from the prior naming requests. Those flags are not a semantic classifier: a matching word may be coincidental, and unflagged replies can still echo prior messages.

Four diagnostic pairs compare the original name/brevity request with no prior message. As in the earlier review, hypothetical anecdotes can become claimed memories even without prior-user text. Stale-message copying therefore does not explain every grounding failure. Fresh-topic wording in the briefs remains insufficient; a coordinated compiler/model adherence investigation is still needed. This branch does not remove history, alter standing preferences or change follow-up behavior.

## Evidence and reproduction

- [All final briefs and eligibility](inventory.md).
- [All main transcripts and history controls](transcripts.md), verbatim.
- [Machine-readable summary](sample-summary.json), with editorial groups, paired-sample similarity and evidence hashes.
- Full outgoing requests: `/home/sean/Work/character-cards-atmosphere-samples.json`.
- Earlier structural-pass raw evidence remains at `/home/sean/Work/character-cards-48-final-samples.json`; the previous report and samples are also retained in commit `e60708a`.

With the installed models and an existing local endpoint:

```bash
EDGELOOP_LIVE_ACCEPTANCE=1 python -m tests.fork.character_cards_smoke \
  --url http://127.0.0.1:11435 --diagnostics \
  --output /tmp/character-cards-atmosphere-samples.json
```

`--resume` validates the same base, model identities and briefs before retaining complete scenarios; partial scenarios are archived and restarted. The harness neither starts Ollama nor installs models.

Changes are confined to `feature/character-cards`. No merge, push or release was performed, and Claude's upstream integration worktree was not modified.
