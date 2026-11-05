# Card-only context separation implementation

Baseline: `test/character-cards-v050` at `07f9d5d`. The production change is confined to the existing `ContextCompiler.compile.assemble()` function. No new context subsystem, settings, scheduling rules or filters were added.

## Change

On deck-card generations, selected narrative excerpts and earlier non-standing user quotations now occupy one **ephemeral assistant-role context message**, with their existing “already answered/background only” and “fallible fiction/not session facts” labels. The latest provider user message contains the active card instruction, verified facts and any standing user directives. A card with no selected context still sends two messages.

The same assembler serves Character, Common, Arrival, Opening, Closing and mission cards. Separation applies when `deck_card` is present, avoiding a new audience-dependent conversation rule. Existing history eligibility and journal permissions are unchanged: Arrival still gets no raw transcript or unauthorized figures, while permitted story context is now outside its active instruction.

Non-card compilation is unchanged, including real-user requests/recall, ranked history, narrative memory and event turns without a deck card. No synthetic context message is written into stored conversation or narrative memory. Verified Director facts, event selection/priority and protective instructions remain in their original paths. The existing assembler token estimate counts the added role overhead, and its existing hard-budget checks still apply.

Production diff: **10 added / 4 removed lines in one file**, including comments. The remaining changes are tests, local capture/evaluation helpers and this report. No card brief or metadata was changed.

## Implementation parity before sampling

The [capture helper](../../../tests/fork/capture_card_context_implementation.py) reconstructs the original synthetic scenarios through real `ConversationService` using recorded earlier replies/card replies. It compiles each initial card request with both the baseline compiler and the implemented compiler on identical inputs. Only `/api/show` reads the installed identities; capture itself uses mocked inference and no hardware.

Results:

- All **96 baseline wire requests exactly reproduced** the original frozen provider requests.
- All **96 implemented requests exactly matched** B from the previous role-separation experiment, including the four unchanged no-prefix controls.
- Every non-card setup request compiled identically in both versions.
- The sampling harness now accepts this capture and uses `implemented_request` directly for B. It does not substitute the experiment's string splitter for the production compiler.

The source remains `/home/sean/Work/character-cards-v050-validation/real-character-cards.json`, SHA-256 `f9eceb3f4440804bbcf4e69e8d8956eaf72d459a67e6a179f7f3950fdaca9ec5`. Full implementation capture is `/home/sean/Work/card-context-implementation/compiled-cases.json`.

## Two-seed simulator evaluation

The [validation protocol](PROTOCOL.md) was recorded before this new sampling run. All 48 Character Cards × two fixed active-session scenarios × two variants × two seeds = **384 new model generations**. Same four installed F29 models, native identities, Director facts, original personal briefs and model options as the investigation; Ollama on `127.0.0.1:11435`. Synthetic RUNNING sessions use early count 2 / established count 5, advancing counters and simulator-sourced HR 90. No physical hardware, tools or agent session-control requests.

Seeds: 271828 and 314159, paired across arms with alternating AB/BA order. Context 8192, max generation 384, threads 8, temperature 0.4, top-p 0.95, top-k 20, repeat penalty 1.0, thinking off. These are initial-response prompt replays, not final delivery/retry acceptance rates.

All **384 request hashes, raw outputs and displayed outputs exactly match** the earlier experiment for the same case/arm/seed. All responses stopped normally, with no thinking content, provider failures or truncation. All eight paired no-history controls are identical. [Reproducibility evidence](evidence/reproducibility.json) records this verification.

| Metric | A: baseline | B: implemented |
|---|---:|---:|
| Literal stale markers, seed 271828 | 26/96 | 1/96 |
| Literal stale markers, seed 314159 | 31/96 | 2/96 |
| Literal markers, both seeds combined | 57/192 (29.7%) | 3/192 (1.6%) |
| Semantic stale echoes, first seed | 26/96 | 1/96 |
| Invented history, first seed | 5/96 | 8/96 |
| Unsupported inference, first seed | 27/96 | 32/96 |
| Card adherence 2/2, first seed | 40/96 | 46/96 |
| Card adherence 1/2, first seed | 50/96 | 49/96 |
| Card adherence 0/2, first seed | 6/96 | 1/96 |
| Mean adherence, first seed | 1.354/2 | 1.469/2 |

| Companion | Literal stale markers, seed 271828 A → B | Seed 314159 A → B |
|---|---:|---:|
| Daisy (`daisy-narrative-f29-v014:latest`) | 3 → 0 | 3 → 0 |
| Evelyn (`evelyn-narrative-f29-v013:latest`) | 6 → 0 | 5 → 1 |
| Celeste (`celeste-narrative-f29-v012:latest`) | 5 → 1 | 11 → 1 |
| Nova (`nova-narrative-f29-v011:latest`) | 12 → 0 | 12 → 0 |

Each companion has 24 cases per arm per seed. Across seeds, 54 paired cases lose an echo, three echo in both arms, and none acquire a new literal echo. In the first-seed quality review, adherence improves in 22 pairs, worsens in 13 and is unchanged in 61. Metrics are reported separately; they overlap and must not be summed. Invented history and unsupported inferences have **not** improved.

Because every displayed reply and the entire review packet/key exactly repeat, the first-seed semantic/quality ratings reuse the original frozen 192 annotations, as specified before sampling. This is **not a fresh independent review**. The original review was one assistant analyst blinded to arm, with subjective/ambiguous judgments; the replication seed has literal-marker evaluation only, not manual quality ratings. Do not infer general reliability or statistical significance from this clustered fixed set. Full definitions and per-model/per-route ratings are in the [summary](evidence/summary.json) and [original protocol](../dialogue-context-ab/PROTOCOL.md).

## Tests

- **754 focused tests passed**, covering compiler/context/card/character/narrative/Director/deck content and the new boundary cases.
- **613 Arrival/correction and new-boundary tests passed**, retaining journal redaction and stored-transcript protections. This overlaps the full suite; do not add these counts together.
- **Full Python: 2,971 passed**, one existing Starlette/httpx deprecation warning.
- Engine JavaScript (`npm test`): **1,477 passed**, zero failures, cancellations or skips.
- Companion JavaScript: **75 passed, one known failure** — presentation aliases actual 26 / expected 25. No new failures in this suite.

Twelve new compiler tests cover answered requests with/without assistant replies, combined raw/narrative contamination, narrative-only context, standing directives, ranked history, no-history cards, hardware boundary retention, budget accounting and three complete-message non-card golden digests captured from baseline `07f9d5d`. Existing card and Arrival assertions were updated to check the intended role separation instead of expecting historical context in the current user message. Arrival tests also assert that the ephemeral context is absent from stored transcript.

The initial broader run exposed ten old Arrival layout assertions; all passed after expectation updates. No production change was needed to address them. A sandboxed engine-JS run stalled on local socket fixtures and was interrupted; its final result uses the run outside those sandbox restrictions. Browser end-to-end tests were not rerun for this compiler-only change.

## Preserved content and boundaries

The entire deck is byte-identical to baseline: **48 Character Cards (12 each), 19 Common Cards**, SHA-256 `39e04b7cc5362b3c83ca56b9d6c06d9a24a74da79bf07326003cf46eba95c1cb`. Personal briefs, IDs, eligibility, mission sequences and shuffle configuration are untouched.

Model-store audit: the same **78 files**, identical sizes/mtimes and identical manifest hashes before/after. Large blob contents were not rehashed. No model creation, pull or Modelfile edit occurred. The temporary local Ollama server used for this run was stopped afterward. Native identities match the frozen request source.

Only the compiler assembly function changed in production. Director priorities, safety/control/device modules, modes, video/script playback and agent-control configuration are untouched. Development remains at `48530582236b1c6dd2f424569fd802ba8217a658`. [Integrity evidence](evidence/integrity.json) and artifact checksums are included.

## Representative output and remaining concerns

The [investigation report](../dialogue-context-ab/README.md#representative-paired-transcripts) contains full displayed paired replies for all four companions and residual failures. Exact repeat verification for this implementation run is reported above. The local `results.json` preserves every new raw/displayed reply and request hash.

The fix reduces old naming-task callbacks. It does **not** resolve unsupported physical/personality claims, fabricated past encounters, question overuse or conflicting affirmative/negative constraints inside some personally authored briefs. The unsupported simulated-HR inference in an identical-prompt control remains. No briefs were rewritten to conceal these issues, and no output filtering was added. Context-role separation is a narrow stale-message mitigation, not a general grounding fix.

## Local reproduction and evidence

Run from the worktree root, with the existing local Ollama service available on port 11435:

```sh
git show 07f9d5d:companion_ai/context_compiler.py > /tmp/edgeloop-baseline-compiler.py
.venv/bin/python -m tests.fork.capture_card_context_implementation \
  --source /home/sean/Work/character-cards-v050-validation/real-character-cards.json \
  --baseline-compiler /tmp/edgeloop-baseline-compiler.py \
  --output /tmp/edgeloop-compiled-cases.json
EDGELOOP_LIVE_ACCEPTANCE=1 .venv/bin/python -m tests.fork.dialogue_context_ab \
  --source /home/sean/Work/character-cards-v050-validation/real-character-cards.json \
  --compiled-cases /tmp/edgeloop-compiled-cases.json \
  --output /tmp/edgeloop-card-context-rerun
```

Use a fresh output directory to preserve the existing evidence. Raw local evidence: `/home/sean/Work/card-context-implementation/` contains capture, exact cases, all 384 new replies, metadata, scoring/reproducibility evidence, model-store audit and regression logs. Selected summaries/checksums/logs are checkpointed in `evidence/` alongside this report.

No development merge, push, export or publication. The local checkpoint is for review; further dialogue changes require a separate decision.
