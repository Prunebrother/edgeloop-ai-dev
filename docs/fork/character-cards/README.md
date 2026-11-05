# Character Card revision and expansion — review handoff

The normal deck now contains **19 Common Cards and 48 Character Cards**, twelve per companion. This combines the revised creative brief with the later request for 48 total: the eight older character cards count toward that total, rather than adding twelve on top of them. Relative to commit `78283d8`, twenty-four briefs are revised and sixteen cards are added. Eight older cards remain unchanged.

The content and regression work is complete on the isolated `feature/character-cards` branch. **Live dialogue quality is not approved for integration.** The local models still answer stale messages, invent history and infer participant qualities without evidence. Nothing was merged or pushed.

## Inventory and draw proportions

| Normal cards | Before this revision | Final |
| --- | ---: | ---: |
| Common | 19 | 19 |
| Nova | 8 | 12 |
| Daisy | 8 | 12 |
| Evelyn | 8 | 12 |
| Celeste | 8 | 12 |
| Entire normal library | 51 | 67 |

One selected companion has a library of 31 normal cards: nineteen Common and twelve of its own. The nominal library split is 61.3% Common / 38.7% Character, **not the actual draw split**, because state, counters, conversation and HR determine eligibility. Other companions' cards never enter its queue.

For Nova, with a fixed RUNNING state, two edges, 600 seconds and no conversation history:

| Available evidence | Eligible Common | Eligible Character | Total | Common / Character across a full cycle |
| --- | ---: | ---: | ---: | --- |
| No HR signal | 11 | 12 | 23 | 47.8% / 52.2% |
| Current rising HR trend | 12 | 12 | 24 | 50% / 50% |

These are cycle proportions for an unchanged eligibility state, not independent probabilities for every successive draw or wall-clock airtime predictions. The existing follow-up card can add another eligible Common Card when conversation is available. State changes and higher-priority lanes alter the observed mix. Opening, closing, three arrival cards and three mission steps are separate shared lanes, excluded from these normal-deck counts.

The [complete inventory](inventory.md) groups each companion into four personality/worldbuilding, four session/project and four playful cards. These are editorial classifications only. No categories, weights or scheduling rules were added to the runtime schema.

## Content decisions

Nova combines synthetic independence, human unpredictability, mischievous inventions and a research-partner perspective. Daisy connects farm independence and family legacy to the voluntary program, with practical humor and personal hopes. Evelyn returns to Asterion, research ambition and uncertainty; one off-duty botany card remains. Celeste combines mission stakes, high standards, ambition, reluctant appreciation and verbal challenges.

Most revised briefs request statements or punchlines. Invitations are optional and challenges are verbal. Flirtation is non-graphic: Evelyn's after-hours invitation concerns imaginary chocolate, not a bodily-fluid procedure; Nova's intimacy-adjacent premise concerns affectionate curiosity about closeness. Celeste's challenge asks for a compelling sentence, not physical exertion.

All forty expansion cards are ordinary RUNNING cards with default repetition and memory=none. They require no measurements or recorded history. The eight older cards retain their original eligibility and fact selection, including Evelyn's HR dependency. Briefs distinguish hopes, opinions and hypothetical institutional scenes from measured outcomes. Mean character-card brief length is 282 characters; every brief fits the existing 400-character limit.

The nineteen Common Cards, eight legacy Character Cards, schema version, deck revision, other lanes and mission definitions were compared with `78283d8` and are unchanged. No production Python or JavaScript, scheduling, compiler, device-control code, model definitions or persistent settings changed. Claude's upstream integration worktree was not modified.

## Validation

**882 focused regression tests passed**, with one existing FastAPI/Starlette test-client deprecation warning. `git diff --check` is clean.

```bash
python -m pytest -q \
  tests/ai/test_character_cards.py \
  tests/ai/test_event_deck_content.py \
  tests/ai/test_event_deck.py \
  tests/ai/test_card_prompt.py \
  tests/ai/test_event_deck_integration.py
```

The tests cover the exact 48-card inventory, global ID uniqueness, original Common inventory, character/model eligibility, two complete unweighted shuffle cycles at three session states, exclusion of foreign cards, in-flight blocking, idempotent delivery, new-card RUNNING eligibility, memory boundaries and real service/compiler composition. A regression test verifies that answered user text is labelled background; it does **not** claim that a real model obeys the label.

The expanded live harness generated **96 main samples: two for every card**, plus eight completed history-control samples. All 96 main samples delivered, with zero conversation errors or final suppressions. Their 101 provider calls include bounded retries. The raw audit reports 133 calls including user replies, controls and an archived partial attempt; those are not 133 independent card samples.

Two main scenarios begin at two edges / 600 seconds and five edges / 1300 seconds. Both are RUNNING, with fresh validated Replay observations. The second coverage order is reversed. Each scenario first answers an unrelated boat-name or café-name request; no further participant replies are supplied. A continuously available simulator supplies timestamped HR. Exact counters, samples and provider requests are retained per turn. No physical person, sensor or device supplied evidence. The harness isolates one card at a time for coverage; the regression suites test the real standard shuffle separately.

The four installed F29 models are `nova-narrative-f29-v011:latest`, `daisy-narrative-f29-v014:latest`, `evelyn-narrative-f29-v013:latest` and `celeste-narrative-f29-v012:latest`. Inference used the real ConversationService/compiler, temperature 0.4, thinking off and no tools. The audit allowed only `/api/show`, `/api/ps` and `/api/chat`. No model was pulled or rebuilt. The temporary loopback Ollama server was stopped afterward.

Two earlier 24-card revision passes were retained locally. The first 48-card attempt stopped because removing the synthetic HR sensor correctly activated disconnection gating. A subsequent partial attempt stopped because the generated trend did not satisfy the old HR card's eligibility. The harness now supports validated resume: it retains complete unchanged runs, archives partial runs and restarts them. The final evidence retains the interrupted row rather than disguising it as a completed run. Most retained scenarios used rising/falling synthetic samples; resumed scenarios used steady samples. Per-turn evidence is authoritative.

## Live quality findings

| Companion | Main samples | Replies containing a question | Prior-message marker flags |
| --- | ---: | ---: | ---: |
| Nova | 24 | 11 | 13 |
| Daisy | 24 | 6 | 4 |
| Evelyn | 24 | 5 | 6 |
| Celeste | 24 | 11 | 7 |
| Total | 96 | 33 | 30 |

Thirty replies end in a question. Mean length is 34.3 words, with a 20–53-word range; 57/96 replies meet the compiler's 15–35-word target. No normalized exact duplicate pair appeared within any companion across its 24 main samples, but similar openings and rhetorical structures persist. These descriptive results use different cards and contexts from the original 24-card review; they are not a controlled improvement estimate or a reliability claim.

Marker flags are a review aid, not a semantic classifier. Matching an anchor word does not prove contamination in every case, and unflagged replies can still echo a previous message. Manual review finds unmistakable examples: Nova's research-partner card names the paper boat, Evelyn's research-appetite card answers the boat choice, and Celeste's mission-stakes card chooses the café name.

Additional material failures remain:

- Daisy turns hypothetical gate scenes into remembered repairs, invents family sayings and in one reply implies her father is dead, contrary to the supplied background about his illness.
- Evelyn claims secured collection/protocol/results and infers a physiological pattern from an engine edge tally. These are not established by the supplied synthetic evidence.
- Celeste infers composure, patience and personal qualities; the mission challenge sometimes becomes a judgment of worth or virility instead of the requested optional verbal task.
- Nova invents perceptions or a current location and sometimes substitutes an answered naming task for the intended topic.

Mechanics success therefore does not establish factual or creative acceptance. No hardware-control API was exposed, and the new-card regression tests verify no Story Memory developments are written; the delivered language itself still needs work.

## Previous-message investigation

The default compiler uses `last_user` history. It omits old companion replies, but copies earlier answered user text into the current provider user-role block, labelled “already answered; background only, do not answer it again.” The current task is another part of that same block. Recorded prompts show the stale naming requests are still visible at generation time. This is a plausible contributor to the observed echoes, not proof that every error has the same cause.

Four control pairs compare the original name/brevity request with no earlier user message. On Nova's borrowed-wonder control, both avoid the unrelated boat/café task. Daisy and Celeste still convert hypothetical anecdotes into claimed past events without prior-user context. That separates an independent tendency to invent biography/history from stale-message copying. Eight controls are too few for a causal or quantitative reliability conclusion.

A fresh-topic instruction was added to revised briefs and resampled, but did not reliably prevent contamination. When history is present, the compiler also permits a short question even if a brief asks for statements. No engine/compiler change was attempted in this content branch. A separate coordinated compiler/model adherence investigation is warranted before treating this pack as ready to integrate; removing all history indiscriminately would also break intentional follow-up behavior and standing preferences.

## Evidence and reproduction

- [All final card briefs and eligibility](inventory.md).
- [Complete main transcripts and history controls](transcripts.md), verbatim and including failures.
- [Machine-readable sample summary](sample-summary.json), including editorial groups and paired-sample similarity.
- Full outgoing requests and archived partial attempt: `/home/sean/Work/character-cards-48-final-samples.json`. Its SHA-256 is recorded in the summary.
- Earlier local attempts: `/home/sean/Work/character-cards-revision-samples.json`, `/home/sean/Work/character-cards-revision-final-samples.json` and `/home/sean/Work/character-cards-48-samples.json`.

With an existing local endpoint and the installed models:

```bash
EDGELOOP_LIVE_ACCEPTANCE=1 python -m tests.fork.character_cards_smoke \
  --url http://127.0.0.1:11435 --diagnostics \
  --output /tmp/character-cards-48-samples.json
```

Add `--resume` only to resume the same briefs and model identities in that output file. The harness checks completed sample briefs against the current deck and restarts incomplete scenarios. It does not start Ollama or install models. Two samples per card are coverage evidence, not a quality guarantee.

Stop here for review. No merge, push or release has been made. Any later integration should merge entries by unique ID and preserve concurrent upstream changes, rather than copying the whole deck.
