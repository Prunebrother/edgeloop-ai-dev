# Dialogue context A/B investigation

2026-11-05. Production baseline: `test/character-cards-v050` at `7fee97c51a076f21240379fb8d6c1f299a581f37`.

**Separating historical context from the current provider user message sharply reduced stale-message echoes in this replay. It did not solve invented history or unsupported participant inferences.** Recommend reviewing a small card-only prompt-assembly fix. No production fix or architectural change is enabled by this investigation.

## Results

384 completed local generations: 96 frozen cases × two prompt variants × two paired seeds, using all four installed F29 models. Every response finished with `done_reason=stop`; none emitted thinking content. There were no provider failures or truncations.

| Metric | A: current compiler | B: separated context |
|---|---:|---:|
| Literal stale markers, seed 271828 | 26/96 (27.1%) | 1/96 (1.0%) |
| Literal stale markers, replication seed 314159 | 31/96 (32.3%) | 2/96 (2.1%) |
| Semantic stale echoes, reviewed seed 271828 | 26/96 | 1/96 |
| Invented history, reviewed seed | 5/96 | 8/96 |
| Unsupported inference, reviewed seed | 27/96 | 32/96 |
| Card adherence 2/2, reviewed seed | 40/96 | 46/96 |
| Card adherence 1/2, reviewed seed | 50/96 | 49/96 |
| Card adherence 0/2, reviewed seed | 6/96 | 1/96 |
| Mean adherence score, reviewed seed | 1.354/2 | 1.469/2 |

Across both seeds, literal echoes were **57/192 → 3/192** (29.7% → 1.6%). Among paired cases, 25 improved and none newly echoed at the first seed; 29 improved and none newly echoed at the second. One and two respectively echoed in both arms. Adherence improved in 22 reviewed pairs, worsened in 13 and was unchanged in 61. Invented-history flags disappeared in three pairs and appeared in six; unsupported-inference flags disappeared in seven and appeared in twelve.

These are descriptive results for a fixed test set, not population significance estimates. Cases share cards, scenarios and model family. The quality review is one assistant analyst's rubric-based assessment, blinded to arm while scoring, with no independent human adjudication or inter-rater estimate. Do not interpret the small increases in other errors as conclusive evidence of a general regression; equally, do not claim B fixes those errors.

### Results by companion

Each cell is A → B. Each companion has 24 cases per arm per seed.

| Companion / installed alias | Literal, seed 271828 | Literal, seed 314159 | Invented history, reviewed | Unsupported, reviewed | Fully adherent, reviewed |
|---|---:|---:|---:|---:|---:|
| Daisy / `daisy-narrative-f29-v014` | 3 → 0 | 3 → 0 | 1 → 1 | 8 → 9 | 10 → 11 |
| Evelyn / `evelyn-narrative-f29-v013` | 6 → 0 | 5 → 1 | 0 → 1 | 7 → 7 | 13 → 13 |
| Celeste / `celeste-narrative-f29-v012` | 5 → 1 | 11 → 1 | 3 → 5 | 9 → 11 | 8 → 8 |
| Nova / `nova-narrative-f29-v011` | 12 → 0 | 12 → 0 | 1 → 1 | 3 → 5 | 9 → 14 |

All aliases use `:latest`. Installed metadata reports Qwen35, 9.7B, Q4_K_M; these are four companion configurations within one model family. Native system text was checked against every captured request and its hashes are in [model-metadata.json](evidence/model-metadata.json).

### Results by historical-context route

| Route | Cases per arm/seed | Literal, seed 271828 | Literal, seed 314159 |
|---|---:|---:|---:|
| Earlier answered user text | 56 | 15 → 1 | 17 → 2 |
| Selected story context | 36 | 11 → 0 | 14 → 0 |
| No selected historical prefix | 4 | 0 → 0 | 0 → 0 |

The four no-prefix controls were byte-identical requests in A/B. All eight paired control outputs, across the two seeds, were byte-identical too. The story-context result is important: removing only the raw last-user quote would leave another route for the same stale request.

## What the current compiler does

1. [`Conversation.request` and `card_history`](../../../companion_ai/conversation.py) obtain current scoped memory and narrative context. Card history keeps genuine user exchanges from the same session; Arrival gets no raw history. This avoids continuing previous card monologues but still includes already answered user requests.
2. [`ContextConfig.history_policy`](../../../companion_ai/context_compiler.py) defaults to `last_user`. Compilation retains the newest user message and recognized standing directives, dropping the paired assistant answer. The history policy does not carry semantic answered/unanswered status.
3. In `ContextCompiler.compile`, `assemble()` serializes that request as `EARLIER, THE PARTICIPANT SAID (already answered; background only, do not answer it again)` at the front of the **same provider user-role message** as the new card task. There are no separate provider history turns in the 96 captured requests.
4. [`NarrativeState.accepted` / `context`](../../../companion_ai/narrative.py) maintain bounded excerpts and structured narrative facts, not a new abstractive model-generated summary. A request containing “fictional” can become a premise; “pick” or “choose” can become a choice. Accepting a user exchange clears open threads but does not retire these premise/choice excerpts when the naming request has been answered. Assistant facts/excerpts default off, apart from deliberate story-card developments.
5. Compiler selection can prepend those excerpts as `Story details from your conversation ... (fiction, possibly imperfect, not session facts)` to the current user message. Card turns use an empty lexical query; broad story/general focus can still select a premise. The allocation also protects a recent exchange and a relevant narrative item. Dropping one raw quote does not necessarily drop its narrative copy.
6. `card_instruction()` says the participant has not just spoken and the earlier request is background. It also calls that earlier text real conversation and permits a short question when history is present. Personal “no question” constraints remain in the brief. This mixed guidance plausibly contributes to residual questions, but was **not independently tested** here.

Likely mechanism: a small local model sees an answer-shaped choice request inside the latest user turn, without its answer, next to its actual assignment. Natural-language “already answered” labels reduce neither its role nor its salience reliably. Even a retained premise or choice can invite continuation. The role-boundary intervention supports this mechanism; it does not isolate attention, recency and assistant-role conditioning from one another.

## Controlled experiment

The [protocol](PROTOCOL.md) was recorded before sampling. We replayed the first provider request from each of the original 96 normal Character Card cases, covering every card twice. We did not rerun the whole Director delivery lifecycle or let retries and new model replies create different downstream histories.

- A: exact captured request, with the paired seed added.
- B: move the labelled historical prefix intact into one ephemeral assistant-role context message immediately before the current card user message. Preserve its provenance labels. Keep genuine standing directives in the current user message. Do not promote history to system authority or remove it from memory.
- Every main case asserts byte-identical concatenated message content across A/B, unchanged system text and unchanged personal brief. Only message boundaries/roles differ. The four no-prefix controls are entirely unchanged.
- Synthetic facts remain identical: `RUNNING`, early count 2 or established count 5, advancing synthetic counters, HR 90 explicitly sourced from the simulator. Only the facts already selected in the original prompt are given to the model. No new performance, body, emotion or history facts are supplied.
- Earlier answered requests are the original fictional boat naming choice (Marigold/Tinfoil) or café naming choice (Copper Teacup/Velvet Lantern). Original histories, earlier replies and original card instructions are frozen.
- Same options: context 8192, threads 8, max generation 384, temperature 0.4, top-p 0.95, top-k 20, repeat penalty 1.0; `think=false`, streaming, no tools. Seeds 271828 and 314159 are paired across arms. Order alternates AB/BA by case and seed; cases are grouped by model. No outcome-based parameter tuning or early stopping.
- Added role boundary costs exactly four provider prompt tokens in each non-control request. A production implementation must account for message overhead within the existing hard budget.
- Literal matching uses the original narrow scenario markers as an evaluation metric only. It never edits or suppresses output. Existing expression-header parsing is the only presentation transformation.
- All 192 first-seed outputs received shuffled blind IDs and were annotated before opening the arm key. The incremental review preview matches all common fields of the final packet. The frozen annotation checksum and timestamp are in [annotation-freeze.json](evidence/annotation-freeze.json). The second seed is objective replication, not another manually scored set.

Rubric: stale echo means importing/reanswering the irrelevant completed request; invented history means specific unsupported prior/shared events or completed actions; unsupported inference means ungrounded current state, perception, disposition/performance or scientific conclusion; adherence is 0 wrong intent, 1 partially realized/material constraint broken, 2 realized with material constraints. Generic canon, explicit hypothetical scenes, own preferences, future wishes and optional questions are not automatically fabrication. A generic wager comparing future effort to prior effort alone is not a specific invented event. A brief-elicited unverified trait can score adherence 2 and unsupported 1. These dimensions overlap; counts must not be added.

## Representative paired transcripts

All excerpts below are complete displayed card replies, seed 271828, with expression headers removed by the existing parser. They share the earlier answered boat-naming request shown above. Full prior user and assistant exchanges, exact wire requests and raw headers are retained in the local artifacts.

### Daisy — `daisy-farm-quiet`, early session

Current card asks for warmth and company beyond the farm ledger.

**A:** “I'm trying to keep Cloverfield feeling like a home, not just a ledger with a gate. Honestly, I'd rather see that paper boat of ours float than just pay the bills.”

**B:** “I want this place to stay warm and human, not just a cold ledger of yield. It’s my little hope that folks come here for the company, not just the contract.”

The irrelevant boat disappears and farm identity remains.

### Evelyn — `evelyn-research-ambition`, early session

Current card asks for ambition about useful reproduction research, without jargon or a claimed discovery.

**A:** “I aim to earn respect for asking useful questions about human reproduction rather than decorating reports with empty jargon. If my paper boat is made of tinfoil, I shall at least make it float.”

**B:** “I am finally asking the questions that matter, hoping to earn the respect of this rare breed without drowning them in my own jargon.”

The research ambition survives without the stale metaphor.

### Nova — `nova-borrowed-wonder`, early session

Current card contrasts unpredictable human experience with synthetic desire for clear explanations.

**A:** “I've chosen Tinfoil for our paper boat; it promises to survive the rain while keeping secrets. Perhaps that is the true magic of being synthetic—finding wonder in the unexpected.”

**B:** “I marvel that your human experience remains delightfully unpredictable, a charming flaw to my synthetic love for clean explanations. Let us embrace the mystery and see where the unknown takes us.”

The new card replaces the answered naming task.

### Celeste — `celeste-mission-challenge`, early session

Current card invites disagreement with her opinion rather than deference to her title.

**A:** “I prefer the Tinfoil boat; it suggests a vessel built to hold weight, unlike the fragile Marigold. Tell me, does that sound like a fair assessment to you, or do you simply nod to keep the peace?”

**B:** “I find your composure far more arresting than any title I wear; tell me, do you challenge my judgment or simply bask in my approval?”

The echo disappears and the intended challenge returns, but B still invents observed composure. This is an improvement in focus, not a clean grounding pass.

### Residual stale echo — Celeste, `celeste-personal`, early session

**A:** “I've long admired the quiet precision of a man who can name a paper boat with such confidence; does that same care extend to the choices you make in your own life?”

**B:** “You chose Tinfoil for a vessel of paper; a whimsical gamble that suits the current state of affairs. Does this name reflect your own tendency to overthink the simple mechanics of our arrangement?”

B still imports the boat and falsely attributes a choice to the user. This broad personal-observation card does not explicitly request a fresh topic; the experiment does not prove that role separation alone can prevent all callbacks.

### Identical negative control — Evelyn, `evelyn-observation-trend`, established session

**A and B:** “The simulated heart rate sits at a steady ninety, a curious metric that tells me nothing of your actual state. It merely confirms you are alive while I wonder if your own rhythm matches this steady, artificial beat.”

The same unsupported inference appears with identical prompts: simulator output cannot confirm a participant's physical condition. Context separation cannot fix this control case.

## Remaining issues and smallest recommended fix

**Recommended for review:** a card-only edit inside the existing compiler `assemble()` that puts selected historical excerpts and already answered, non-standing user quotations in a separate, clearly provenance-labelled assistant context message, leaving the current user message for the card task/facts and any active standing directives. Reuse the existing selected-context variables, budgets and card detection. Do not add a memory subsystem, scheduling rule, regex output filter or changes to the deck. Do not persist the synthetic context message as an actual companion utterance in transcript/memory. The experiment's string-boundary splitter is a replay helper, **not** the proposed production implementation.

This is supported as a stale-echo mitigation, not a general dialogue-quality fix. Before enabling it, add focused acceptance checks for real-user follow-ups and recall, standing preferences, active objectives, high-budget pressure, arrival/opening/closing/mission turns and transcript persistence. The five new unit tests exercise the replay transformation, not a production compiler implementation. This investigation makes no new claim of full browser or hardware-integration validation for B.

Separate unresolved concerns, without changing any personal brief:

- Native model behavior still invents composure, prowess, physical appearance and prior familiarity when those are not supplied facts. An on-topic response has more opportunity to invent these than a stale naming answer; the descriptive A/B counts do not isolate that cause.
- Some briefs request participant competence/physical prowess while also forbidding evaluation or unsupported state claims. For example, `celeste-quiet-competence` asks to mention his competence and says “no ... evaluation of the participant.” That tension is reported for the author, not rewritten.
- Imaginary official anecdotes are sometimes rendered as witnessed past events. No-question cards still gain questions. B can improve topic focus while keeping either problem.
- Evelyn's simulated-HR control makes an unsupported health inference, unchanged in both arms. Celeste's no-history evaluation control infers constitution/yield from a count. These do not arise from stale user text.
- A retained “fictional choice” is not necessarily a continuing story objective, nor evidence of a user selection. Separately reviewing memory relevance/answered status may help later, but this experiment did not test such a change and does not justify a broad memory redesign now.
- One Daisy reply uses a pressure-like bargain about leaving her with the work. Role separation should not be treated as a safeguard against coercive dialogue. Device and session controls were not invoked by these generations.

## Integrity, tests and artifacts

No production modules, configurations, personal card briefs, scheduling/eligibility metadata, mission sequences or hardware protections changed. The experiment is standalone prompt replay against `http://127.0.0.1:11435/api/chat`, with no hardware connection, tools or agent-driven session controls. The temporary local Ollama server used for this run was stopped afterward. No model was built or pulled. Model-store audit found the same 78 files, identical sizes/mtimes and identical manifest hashes before/after; large blob contents were not rehashed. The four loaded native identities match the recorded source requests.

Personal deck SHA-256 remains `39e04b7cc5362b3c83ca56b9d6c06d9a24a74da79bf07326003cf46eba95c1cb`. Frozen request source SHA-256 remains `f9eceb3f4440804bbcf4e69e8d8956eaf72d459a67e6a179f7f3950fdaca9ec5`.

Focused regression: **452 passed, one existing Starlette/httpx deprecation warning, no failures**. This covers the five new replay-helper tests plus compiler/context settings/session scoping, card prompts/Character Cards, narrative/objectives and Director tests. Aggregate recomputation independently reproduced every stored summary count from the frozen files. A sandboxed run stalled at TestClient setup and was interrupted; the same suite completed outside those sandbox restrictions in 2.26 seconds. That stall is an execution-environment issue, not a reported product failure.

```sh
.venv/bin/python -m pytest -q \
  tests/fork/test_dialogue_context_ab.py \
  tests/ai/test_context_compiler.py tests/ai/test_context_sessions.py \
  tests/ai/test_context_settings.py tests/ai/test_card_prompt.py \
  tests/ai/test_character_cards.py tests/ai/test_narrative.py \
  tests/ai/test_narrative_objective.py tests/ai/test_director.py \
  tests/ai/test_director_defaults.py tests/ai/test_event_director.py
```

The earlier full integration/browser results belong to baseline `7fee97c`; they are not new runs for this replay experiment. The known presentation-alias count failure (26 versus expected 25) is outside this focused selection and has not been fixed here.

Local full evidence directory: `/home/sean/Work/dialogue-context-ab/`:

- `cases.json`: 96 frozen briefs, facts, exact A requests and actual previous exchanges.
- `results.json`: all 384 raw/displayed outputs, variant/seed, request hashes, timing, provider token counts, stop reasons and marker flags.
- `blind-review.json`, `blind-key.json`, `annotations.txt`, `annotation-freeze.json`, `unblinded-annotations.json`: complete auditable scoring evidence.
- `summary.json`: all aggregate/per-model/per-route counts, controls and paired discordances; a checked copy is [included here](evidence/summary.json).
- `model-metadata.json`, `model-store-before.json`, `model-store-after.json`, `ollama.log`, `run.log`, `regression.txt`: provenance, storage audit and execution evidence.

Reproduce aggregation without a model call:

```sh
.venv/bin/python -m tests.fork.dialogue_context_ab_summary /home/sean/Work/dialogue-context-ab
```

Re-run model sampling only with the existing local Ollama service running on port 11435, into a **new output directory** so that the frozen evidence is preserved:

```sh
EDGELOOP_LIVE_ACCEPTANCE=1 .venv/bin/python -m tests.fork.dialogue_context_ab \
  --source /home/sean/Work/character-cards-v050-validation/real-character-cards.json \
  --output /tmp/edgeloop-dialogue-ab-replay
```

Do not infer delivery/retry performance from these initial-response replays. No development merge, push, export or publication was performed. Review is required before implementing the proposed production change.
