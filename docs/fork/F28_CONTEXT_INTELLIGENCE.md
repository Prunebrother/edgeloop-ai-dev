# F2.8 — Context Intelligence

## Pipeline audit

Baseline: `4b82bb5`, `f2.7-checkpoint`, clean `experiment/ai-companion`. Development remains on this branch; existing user services and in-memory conversations are left running. F2.7 is a software-tested recovery point, not a physical-hardware acceptance claim.

Original browser engine → allowlisted read-only projection → authenticated observer/strict Snapshot → BrowserObservation canonical facts and bounded samples/events → F2.7 deterministic detectors → existing Director → per-model narrative/conversation context → ModelManager composition → OllamaProvider. The provider reads `/api/show` SYSTEM metadata and prepends its exact text to runtime rules; character personality remains embedded in unchanged installed models. Requests explicitly use `think: false`. Reasoning channels are excluded before expression extraction; normal dialogue uses the single F2.5 header protocol.

The original composition included a full fact view (or broad event view), repeated grounding paragraphs, the current prompt, whole bounded narrative context and recent dialogue. Identical story excerpts frequently appeared in history and narrative context. The Director's prose event JSON duplicated typed derived-event evidence. All operational facts were retained by the factual checker, which can still reject a reply after one correction. There is no existing independent character objective structure; motivation is embedded in SYSTEM and story excerpts.

Essential on every grounded call: read-only/current-vs-historical boundaries, simulator/source distinctions, session state, uncertainty about physical movement, current user text, expression format and embedded identity. Frequently relevant: recent user dialogue, agreed choices/commitments. Occasionally relevant: BPM/trends, selections, running ticks, device details, specific milestones. Inappropriate to replay indiscriminately: acknowledged/stale events, old operational claims, abandoned story epochs, duplicate premises, output bookkeeping and raw detector configuration. Director scheduling remains separate from attention.

`canonical_session.facts.seconds` is `state.sessionSeconds`, accumulated RUNNING ticks. It freezes in PAUSED/RAMPDOWN and resets on stop/reset/start. It is not wall-clock duration. Total wall-clock/paused duration is unavailable. Capture timestamps, fact current/known/reason and snapshot age retain F2.3/F2.7 semantics. F2.8 selects timing when requested rather than repeating it on every story turn. No new timer or countdown exists.

## Compiler and budgets

The CPU-only Context Compiler chooses one primary focus, relevant authoritative fields, optional supporting verified events, ranked fictional excerpts and recent scoped dialogue. It consumes the existing canonical contract and stores no new telemetry/history. Full canonical facts remain available for post-generation checking even when not selected for the prompt. Direct user messages take priority; quiet scheduling still belongs to the Director. `compose_legacy` preserves explicit F2.7 fallback behavior for matched comparisons.

Token estimates use max(character count, UTF-8 bytes)/2.5 plus message framing, **not a model tokenizer**. Ollama does not expose a tokenizer through the current provider contract; no second inference is used to count tokens. Embedded SYSTEM, output allowance and framing reserve count against the hard model context. Configurable category allowances control optional history/narrative; essential grounding, requested facts and current user text may exceed soft targets but never silently truncate. An unfit mandatory prompt produces a clear ContextBudgetError. Provider-reported prompt tokens are recorded separately for comparison.

Completed attention, objective, diagnostic and acceptance details follow below.

## Attention and memory lifecycle

A real user turn has one `answer_user` focus; multiple requested facts can support it. A fresh verified trigger can produce `react_event`. A Director-authorized initiative selects one unresolved thread or commitment; without a fresh trigger, event-only composition requests silence. The compiler never schedules inference. Existing F2.7 debounce, coalescing, priorities, user/typing protection, cooldowns, acknowledged-event suppression and bounded queues remain authoritative for scheduling.

Session/source freshness and event age are checked before evidence inclusion. Triggering evidence is compacted once; unrelated events are not added to an ordinary user topic. Historical telemetry dialogue cannot substitute for current values. Explicit historical questions may retain historical quotations, clearly subordinate to the current snapshot. Recent explicit user directives are ranked before optional excerpts and may exceed soft allowances rather than silently losing instructions. Memory disabled, a zero history allowance, or an explicit story-epoch boundary can exclude earlier dialogue by deliberate policy. If required content cannot fit the estimated hard limit, the request fails clearly rather than silently clipping it.

Memory ranking uses topic-word overlap, category priority and recency. Commitments/threads outrank incidental developments; exact excerpts already present in retained dialogue are not duplicated. New-topic requests omit unrelated story excerpts. Explicit, unquoted directions such as “Let's abandon this storyline” establish the existing narrative reset boundary before inference. Negated requests, quoted dialogue and operational stop requests do not become storyline-reset commands. For a fresh premise, superseded abandonment requests and their acknowledgements are omitted instead of becoming the subject again. This is a conservative English pattern policy, not full semantic intent recognition.

Optional objectives live inside the **existing per-model NarrativeMemory**, with ID, fictional premise/motivation, next development, transition condition, phase, status, revision and at most four validated milestone IDs. They are authored/edited through Story Memory, not generated as commands. Lifecycle actions are create, revise, pause, resume, complete and abandon. Completion is a fictional user-directed transition, never proof of an EdgeLoop goal. No default objective or second personality system is imposed on either character. Existing embedded identities determine their interpretation. Objective text rejects operational measurements/safety-bypass instructions; objectives cannot target exceeding physiological limits or ignoring discomfort.

Valid edits cancel pending generation/commentary for that model. Abandonment/new-story resets replace the epoch while retaining the visible transcript and actual EdgeLoop history. Old chats queued behind discovery are also discarded on objective edits; an authenticated race test proves they cannot recreate an abandoned story. Invalid edits retain prior state and work. Ordinary objective persistence follows the existing opt-in local narrative setting; restored active objectives are paused and receive no initiative permission. Default cross-session narrative persistence remains OFF. Explicit reset boundaries are saved even when persistence is disabled so an older opted-in record cannot return.

## Configuration and UI

**Character → Director → Context Intelligence** shows current focus/source, selected fact categories, event IDs, narrative references, excluded events, estimates, actual prompt tokens where available, category usage, omissions, compilation time and applicable objective. It exposes no private reasoning or full transcript. The last compilation is cleared on model switch/story reset/objective edits rather than presented as current work. **Context budgets** provides compiler enable/fallback, soft target, history and narrative allowances. Edits do not generate dialogue and apply to future requests; in-flight requests and their bounded retries use a frozen configuration.

Backend configuration is atomically stored alongside existing settings in `context-intelligence.json`. Defaults, in estimated tokens:

| Category | Default | Allowed range |
|---|---:|---:|
| Total prompt soft target, including embedded identity | 2,800 | 512–7,168 |
| Runtime grounding | 500 | 256–1,200 |
| Requested/current facts | 700 | 200–1,800 |
| Primary focus | 100 | 40–300 |
| Verified event evidence | 400 | 80–1,200 |
| Narrative excerpts/objective | 450 | 0–1,800 |
| Recent dialogue | 1,200 | 0–5,000 |
| Existing expression protocol | 280 | 80–400 |

Grounding/facts/focus/trigger/format allowances are soft and report overruns instead of removing required evidence or changing the expression protocol. Optional history/narrative use their allowances, with explicit recent user directives taking priority. Hard capacity additionally reserves embedded SYSTEM, configured output and framing. Event age is configurable from 5–120 seconds, default 60. Schema version zero receives defaults/version one; invalid or unsupported configuration activates an explicit, visible F2.7 fallback and preserves the file. Model selection cannot change this service-wide configuration or enable thinking.

To compare or recover behavior, uncheck **Use F2.8 compiler** and save. The retained `compose_legacy` assembly is the F2.7 algorithm, using the same unchanged model and current transport/factual protections. All settings can also be submitted through authenticated `configure_context`; schemas are archived in [f28](f28/). Do not edit a live settings file expecting hot reload: use the validated UI/API, or stop the observer before editing its configuration.

## Evaluation and results

The offline harness runs **fifty steps per character per assembly arm**, with **38 completed simulated exchanges** in each arm. It covers greetings, story premise/choices, selections, start, milestones, quiet/initiative, callbacks, pause/resume, actual derived-rise evidence, objective revision/pause/resume, unknown telemetry, model restoration, abandonment, fresh premise, stop, stale state and reconnect. Simulated heartbeats maintain continuity before validated transitions; transport gaps are deliberately separate scenarios. Mock responses prove transport/memory/budget mechanics, not narrative quality. Existing deterministic tests additionally cover current user priority during in-flight events, unknown characters, expression/reasoning isolation, cancellation and hard-budget failure.

Live comparison used the unchanged Evelyn/Daisy narrative models at **11435**, sequentially, with the same synthetic inputs and user prompts. The baseline is the preserved F2.7 assembly algorithm; the offline comparison passes the same optional objective extension to both arms. Response-dependent histories/Director decisions can diverge. Every one of the final run's **45 outbound chat requests** used `think: false` and preserved native SYSTEM verbatim. No new classification/summarization inference was introduced.

| Final paired live sample | F2.7 assembly | F2.8 compiler |
|---|---:|---:|
| Outbound generations | 23 | 22 |
| Completed replies | 19 | 22 |
| Mean actual prompt tokens, all calls | 2,405 | 1,428 |
| Mean actual prompt tokens, 22 common model/scenario pairs | 2,383 | 1,428 |
| Peak actual prompt tokens | 3,207 | 1,645 |
| Mean provider first-token latency | 0.857 s | 0.275 s |
| Mean first visible payload latency | 1.154 s | 0.671 s |
| Mean total attempted-turn latency | 1.943 s | 1.260 s |
| Mean generation throughput | 93.54 tokens/s | 94.51 tokens/s |
| Valid final expression metadata observations | 22/23 | 22/22 |

Aggregate actual prompt usage decreased **40.65%** in this sample. One baseline Daisy response used unsupported `confident` metadata and followed the existing fallback. No expression markers or reasoning appeared in completed dialogue/history. Baseline repetitive responses were suppressed; the compiler arms still respected unsolicited limits instead of forcing every milestone into speech. These are measured mechanics, not proof of emotional appropriateness or better storytelling.

The experiment is small and sequential, with cache/loading, generated text and scheduling differences; it does **not** establish a guaranteed latency improvement. First-visible timing is the backend's first parsed visible-text payload, not browser paint, and can be provisional on a user turn later corrected. Proactive output retains the existing validation hold. GPU end-of-arm snapshots were **8,210–8,213 MiB of 10,240 MiB**; these are not a continuous peak-memory trace, and no VRAM saving is claimed. No simultaneous second resident LLM, embeddings or model build was requested.

On twenty matched synthetic fact fixtures repeated thirty times, compiler time was median **0.356 ms**, p95 **0.572 ms**, versus **0.272/0.485 ms** for the old assembly. The small added CPU cost is independent of inference. Estimated prompt means were 1,493 versus 2,192. The heuristic overestimated actual live prompt counts substantially: raw-wire mean estimate errors were approximately +1,427 tokens for F2.8 and +2,306 for F2.7. Consequently estimates are deliberately conservative and can omit useful memory earlier than a true tokenizer would. No claim is made that estimated hard capacity is tokenizer-exact for arbitrary inputs. Actual provider counts are shown separately; exact local tokenizer integration is a future extension, not another inference call.

**Final regression:** 1,057 upstream tests, 370 Python tests, 30 bridge/presentation tests and seven browser workflows pass. Browser coverage includes dashboard streaming/timing, all 24 portraits/expression mappings, mode/goal/Came Early, narrative/reset/restoration, character menus, Event Intelligence and Context Intelligence. All devices were simulated, denied or intercepted. One existing Starlette/FastAPI deprecation warning remains. Physical-device acceptance is explicitly deferred to the user.

## Quality limitations and manual review

The models retain distinct scientific/farm framing, but still sometimes restate premises, invent object possession, over-explain disconnected equipment, ask unnecessary questions, or avoid a direct timing answer. They can also call an engine counter a simulator artifact or imply comfort/calm without adequate evidence. A smaller prompt did not solve these semantic problems. Live timing mistakes led to focused guards rejecting explicit unsupported wall-clock/paused durations and wrong/stale running-counter claims, using the existing single correction attempt. These regex checks are incomplete; accepted language is not proof of perfect grounding. A separate latest-policy timing smoke is archived alongside the final paired run.

No exact-duplicate flag in the small final accepted sample establishes that repeated themes disappeared. Possession/continuity and emotional expression appropriateness still require human review over longer real sessions. Use F2.7 fallback if the new selection omits a useful callback or harms a particular model. Increase relevant allowances conservatively where appropriate; do not infer safety from sensitivity, character wording or a narrative objective. No operational source or hardware safeguard has been replaced.

Manual rubric (score each dimension separately, with transcript examples): answer relevance to the latest user; correct source/status/timing and event interpretation; no fabricated cause or hardware action; consistency of agreed objects/promises; fresh rather than repeated premise/questions; character distinction; expression suitability; welcomed initiative; recovery after reset/switch/cancel; and latency/context usage. Failed/suppressed responses should be reported separately from successful ones. Subjective intelligence, continuity and physical safety are not automatic pass/fail claims from token savings.

## Reproduce and activate

```sh
cd /home/sean/projects/edgeloop-ai-fork
.venv/bin/python -m pytest -q tests/ai tests/fork
node --test tests/fork/bridge.test.mjs tests/fork/presentation.test.mjs
.venv/bin/python tools/fork_validate.py --tests --report /tmp/f28-upstream.json
.venv/bin/python -m tests.fork.context_evaluation --output /tmp/f28-replay.json
# Optional existing local Ollama evaluation; never starts/restarts Ollama:
.venv/bin/python -m tests.fork.context_evaluation --live --output /tmp/f28-live.json
CONTEXT_BROWSER_REPORT=/tmp/f28-context node tests/fork/context-intelligence-browser.mjs
```

Existing browser commands remain `tests/fork/browser.mjs`, `character-browser.mjs`, `event-reliability.mjs`, `narrative-browser.mjs`, `character-menus-browser.mjs` and `event-intelligence-browser.mjs`; narrative/menu/context workflows share fixture ports 8850/8858 and must run sequentially. Fixtures never connect physical devices.

Active user services were **not restarted**. To activate at a convenient boundary, preserve/export any nonpersistent conversation first, then stop **only the AI observer** in its existing terminal (Ctrl+C). If it is detached, identify that observer using `ss -ltnp 'sport = :8768'` and terminate only its verified `ai_observer.server` PID. Then run:

```sh
cd /home/sean/projects/edgeloop-ai-fork
./tools/serve-ai.sh
```

Keep the EdgeLoop UI and Ollama services running. Reload **http://127.0.0.1:8770/** and pair with **ws://127.0.0.1:8768/observe** using the fresh one-hour key printed by the restarted observer. If the UI server is not running, start it separately with `./tools/serve-local.sh 8770`. No branch migration, model rebuild or new model is required.

Recovery checkpoints on `experiment/ai-companion`: A `ce8b408`, B `f5e61cb`, C `eacb883`, D `d4f4881`, queued-work fix `54b4ac0`, final tag `f2.8-checkpoint`. `f2.7-checkpoint` remains at `4b82bb5`. F2.8 does not alter original engine/driver/safety logic, existing Modelfiles or artwork. Unrelated untracked Celeste narrative source directories appeared during development and are deliberately excluded from these commits.

Evidence: [live summary](f28/live-summary.json), [compilation benchmark](f28/compilation-benchmark.json), [full replay](f28/session-replay.json), [browser results](f28/browser-workflows.json), [diagnostics screenshot](f28/context-browser/context-diagnostics-1920.png), [objective editor](f28/context-browser/fictional-objective-2560.png), [mobile](f28/context-browser/context-mobile-390.png).
