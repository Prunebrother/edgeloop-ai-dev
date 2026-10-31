# F2.8.4.1 — Intelligent memory and reliable recall

Follow-up: [F2.8.4.2 significance-aware memory investigation](F2842_SIGNIFICANT_MEMORY.md) documents the supplied browser regression, the generalized deterministic repair, and the still-blocked live A/B acceptance.

Baseline/starting HEAD: `4b09888` (`f2.8.4-checkpoint`), clean `experiment/ai-companion`. Work stayed on the existing branch. No models, Modelfiles, artwork, installed packages, conversations, journal data, hardware drivers or safety algorithms were changed. No active service was restarted. The service-worker edit only invalidates the public UI cache, with its reviewed manifest hash updated.

**Recommendation: use B, the improved deterministic path.** C, the experimental model-assisted curator, defaults off. The offline comparison demonstrates better evidence retention/selection, not live generated-answer improvement. Browser and Ollama access are blocked in this environment; the live portion of the success criterion remains unverified.

## Findings and repairs

Synthetic reproduction at the actual checkpoint established these failure mechanisms:

1. An unquoted `ORCHID-17` was stored as an ordinary text-derived detail, without an exact identifier slot. Identifier/door questions did not activate explicit recall handling. Routine later user details could evict that record from the sixteen-fact store.
2. `I enjoy tending an overgrown succulent.` was present in Story Memory, but `What is your hobby?` matched neither its wording nor a recognized recall intent. It selected no fact even before retention pressure. Generic hobbies could subsequently be evicted.
3. Full-sentence slots gave contradictory replacement identifiers/hobbies different slots, bypassing the existing first-established-fact protection. Shared user-prompt cues could also make an unrelated character detail look relevant to a door question.

The reported live transcripts were not available as a captured request trace. These are reproduced harness defects, not a retrospective claim that a particular live response followed one proven path.

`narrative_facts.py` now recognizes exact uppercase identifiers such as `ORCHID-17`, object/color anchors and personal hobby statements. Stable slots preserve the original code/detail through routine detours; replacement assistant assertions become conflicts. Explicit user corrections supersede dialogue through the existing merge rules, without overriding recognized native canon. Legacy retained excerpts are reclassified without changing original IDs, wording, speaker, scope or epoch; collisions use the same merge protections.

Recall questions about identifiers and hobbies receive explicit source-based recall/uncertainty instructions. Direct text/slot overlap carries more weight than incidental prompt-cue overlap. Matching established facts take precedence over generic summaries; their source/category, exact wording and hypothetical status remain visible. Ordinary conversation keeps the existing selection/allocation behavior. No global token budget was increased.

A narrow generated-response check catches an explicit replacement identifier during identifier recall. It shares the existing single factual correction attempt and final validation; it does not add another model or a separate retry loop. Creative inventions outside recall remain possible. Hobby meaning is not checked by a general semantic validator, and provisional streamed text can appear before the existing correction/reset mechanism replaces it.

Temporary topic changes did **not** overwrite an existing premise in the inspected `accepted()` path. The premise is assigned only while absent. Tests preserve it across unrelated topics. Session-dependent resets when persistence is disabled remain existing lifecycle behavior, distinct from replacing an active premise. No new premise manager was introduced.

## Optional curator

`memory_curator.py` maintains a bounded, process-local buffer of accepted fictional conversation excerpts. It submits a structured task through the **currently selected ModelManager/provider**, sharing the normal lifecycle and provider locks. The native Modelfile identity remains intact. The request uses `think: false`, JSON-schema output, no tools and no expression protocol. Ordinary character streaming/expressions and sampling presets are unchanged.

The model proposes source references, verbatim quotes, categories, integer importance, retain/omit/contradiction actions and brief justifications. Python validates before applying:

- References must point to supplied memories or registered accepted excerpts, and the quoted source text must match in full. Speakers, scope, epoch and wording come from the source, not model assertions.
- Hypotheses cannot be promoted into established facts. A sourced, non-hypothetical first-person assistant development can be classified as a personal detail; unrelated scenery cannot be promoted this way.
- Operational/physiological assertions and instruction-injection patterns are excluded from curator input/application. Fictional memories do not become Session Journal or authoritative telemetry facts.
- Known identifiers, character details, commitments and explicit corrections cannot be omitted. Routine generic developments may be deprioritized. Contradiction proposals are diagnostic, never authority to overwrite established history or reactivate superseded/conflicting facts.
- Existing deterministic merge/canon protections still apply. Invalid JSON, duplicate keys, schema errors, unsupported additions, stale scope/revision and oversized outputs reject the result. Persistence uses a staged copy and atomic existing-store write; failure preserves deterministic state.

Validated importance affects existing retention/ranking. Source references and justifications are visible in Story Memory; curator status/attempts are shown beside its controls. No raw prompt or private transcript is logged to diagnostics.

Limits: sixteen narrative facts remain unchanged; at most sixteen model/epoch source buffers, twenty-four excerpts of up to 320 characters each, twelve recent excerpts plus sixteen memories per request, six output proposals and 16 KiB parsed output. The curator checks native identity plus task/input against the existing hard context limit, with at most 1,024 output tokens. Oversized inputs fall back rather than increasing context. The default inference timeout is twenty seconds, configurable within 5–30 seconds.

Scheduling is intentionally conservative: configurable **8–12 accepted conversational turns** between attempts, at least ten seconds since the last user request, completed presentation pacing, no conversation generation or Director queue, no queued model requests/selection/typing, and original EdgeLoop status **IDLE**. It never curates while running or paused. User requests, session events, model switches, storyline resets, cancellation and privacy mutations preempt it by cancelling the HTTP task. Failed/cancelled attempts consume their interval, avoiding rapid retry loops. This can postpone useful curation; it prioritizes responsiveness over coverage.

The configuration is local `memory-curator.json` in the existing observer data directory. Enabling it does not enable memory persistence: existing narrative-memory enable/persistence settings still govern storage. Switching it off stops future curation and clears its temporary sources; already validated annotations remain in the existing memory. New storyline resets clear that model’s curator sources and narrative epoch, retaining transcripts and the separate Session Journal. There is no automatic objective creation, second resident model, embedding service or cloud dependency.

## Repeatable browser acceptance

From the repository root, one command launches unique loopback fixture ports, temporary observer storage and the actual browser UI:

```sh
node tests/fork/intelligent-memory-browser.mjs
```

For real conversations using the already-running Ollama service and installed models:

```sh
node tests/fork/intelligent-memory-browser.mjs --live
```

The live runner first checks `http://127.0.0.1:11435` and the three required model names; it never starts Ollama, rebuilds a model or stops a user service. Set `MEMORY_REPORT=/tmp/my-memory-report` to change the report/screenshot directory. `MEMORY_DETOURS` defaults to eight; larger values permit longer stress runs. C needs at least eight accepted replies to trigger; very short custom runs intentionally fail its curation-application acceptance check.

Each command compares A/B/C for Evelyn v1, Daisy v1 and Celeste v2, sequentially. A loads the actual checkpoint extraction, narrative-memory and compiler sources from Git; B uses improved retrieval; C enables the experimental setting through the UI. It pairs the observer, selects the character, starts a storyline, establishes the door clue and a character hobby, sends detours, asks recall questions, applies a correction, inspects Story Memory/Context Intelligence and resets. It checks model scopes and temporary-topic premise continuity. Daisy’s scenario uses wildflowers; Celeste’s uses fountain pens. These are synthetic test developments, not changes to canonical personas.

Hardware APIs are denied in the browser context. The UI’s normal idle/simulated observer projection supplies synthetic session context; the runner never starts a physical session. Temporary test-clock advances avoid the production chat flood limit and lengthy idle waits without changing inference latency measurements. Browser permissions/visuals are real; mock Ollama answers only test plumbing, persistence and context-dependent rendering.

Reports separate exact identifier/string matches, hobby object anchors, candidate unsupported hobby assertions, replacement identifiers, corrections, selected fact IDs, memory size, provider prompt tokens, inference calls, curator calls and wall-clock response latency. Screenshots show memory and compilation diagnostics; pairing inputs are cleared and generated credentials are redacted from failures. Character voice/continuity still requires manual review of the synthetic live responses; keyword scores do not prove personality quality. Completed experiment workflows and recall acceptance are separate fields; B/C recall failures or missing C application produce a nonzero exit.

## Measured results

Artifacts: [comparison](f2841/evaluation.json), [validation](f2841/validation.json), [upstream](f2841/upstream-tests.json), [existing browser attempts](f2841/browser-regressions.json), [A/B/C mock attempt](f2841/browser-mock.json), [A/B/C live attempt](f2841/browser-live.json).

The offline benchmark uses the actual F2.8.4 modules, identical synthetic facts, twenty-four detours, histories, native-source identity lengths and thirty repetitions per compilation. C applies synthetic source-validated importance proposals; this isolates validation/ranking and does **not** measure LLM intelligence.

| Configuration | Relevant evidence in outgoing recall context | Greeting token change | Extra curator inference |
| --- | --- | --- | --- |
| A: checkpoint | 0/6 | baseline | none |
| B: improved deterministic | 6/6 | 0 | none |
| C: improved + synthetic proposals | 6/6 | 0 | real cost unmeasured |

Recall prompts add approximately **242–245 estimated tokens** relative to A. Compilation medians in the saved sample are about **0.71 ms A, 0.77 ms B, 0.77 ms C**. Curator inputs are approximately **3,448–4,876 estimated tokens**, including native identity, in this fixture; synthetic validation/application takes about **0.21 ms median**, excluding model inference and disk persistence. Narrative state remains sixteen facts, approximately 8.5 KiB A versus 9.9–10.1 KiB B/C here. Token estimates use the existing conservative character/UTF-8 heuristic, not a provider tokenizer.

- **1,057 upstream tests pass**, with zero failed files and the reviewed original-file manifest verified.
- **562 Python tests pass**, including 29 new cases for retained identifiers/hobbies, conflicting inventions, corrections, uncertainty, migration, epochs/models, premise continuity, JSON/source/category validation, personal-detail classification, persistence failure, scheduling/preemption, authenticated settings and the actual single-repair generation path.
- Three existing TCP-dependent cases remain environment-blocked: occupied observer port, occupied UI port and desktop HTTP pairing. The unfiltered attempt reproduced two failures and one fixture error with `EPERM`; the final run deselects those three. The previously documented external `/tmp` 20 ms selector polling shim is needed for in-process TestClient under denied asyncio self-pipe writes. Production is unchanged. One existing Starlette deprecation warning remains.
- **44 companion JavaScript tests pass.** The eight existing browser workflows were attempted and blocked before acceptance by local socket/Chromium restrictions.
- The new mock A/B/C runner fails before launching fixtures with **`listen EPERM: operation not permitted 127.0.0.1`**. The live runner’s Ollama preflight is also denied. Zero browser comparisons completed and no screenshots were produced here.
- All **eighteen direct sequential Ollama recall attempts** failed with `ConnectError`. Zero live recall or curator generations completed. Actual answer accuracy, unsupported-invention rate, provider prompt tokens, added inference latency, VRAM and subjective character quality are therefore unavailable.

B is the best supported default: it improves deterministic evidence coverage with no curator inference. C shows no additional benefit in this small synthetic fixture and its live cost/benefit is unproven. Keep it optional/off pending the browser/live comparison.

## Remaining limits and activation

English lexical anchors do not provide full semantic understanding. Identifier patterns, object/color slots and hobby phrasing can miss paraphrases; ambiguous objects, evolving hobbies, implicit references or multiple similar clues still need explicit clarification/corrections. Source validation proves provenance, not the truth or narrative importance of every fictional assertion. Curator classification/importance can be poor despite valid JSON. Native-canon checks cover the existing explicit relationship rules, not an exhaustive semantic canon validator. Hobby-answer meaning is not deterministically proven. No subjective creativity, personality or comprehensive physical-safety validation is claimed.

No running observer was restarted. When ready, manually stop the existing observer and launch the updated one with the **same existing data directory**, leaving Ollama running:

```sh
cd /home/sean/projects/edgeloop-ai-fork
EDGELOOP_OLLAMA_URL=http://127.0.0.1:11435 ./tools/serve-ai.sh
```

Preserve a custom `EDGELOOP_FORK_AI_DATA` value if used. Reload the UI and pair through the existing local flow. Improved deterministic recall is automatic for retained facts; no lost/evicted historical detail is reconstructed from nothing. Experimental curation is enabled explicitly in **Story Memory → Experimental memory curator**.

Other reproducible checks:

```sh
.venv/bin/python tools/fork_validate.py --tests --report /tmp/f2841-upstream.json
.venv/bin/python -m pytest -q tests/ai tests/fork
node --test --test-isolation=none --test-reporter=tap tests/fork/*.test.mjs
.venv/bin/python -m tests.fork.intelligent_memory_evaluation --live --output /tmp/f2841-evaluation.json
```

Implementation commits: `637147a`, `06dde83`, followed by the final source-validation/documentation checkpoint. Tag: **`f2.8.4.1-checkpoint`**. Resolve the exact final commit with `git rev-parse f2.8.4.1-checkpoint^{}`.

## Browser runner progress and timeout controls

The runner prints arm, character, named browser step and conversation turn as it advances. The isolated backend emits inference start/completion/cancellation/timeout events with request number, model, curator flag, elapsed time and terminal token counts. Provider request logs contain metadata instead of prompt bodies, and pairing credentials are redacted. Long waits print a heartbeat every ten seconds; recall/correction results are printed as soon as scored. The same structured events are saved in `MEMORY_REPORT/progress.jsonl`.

Timeout settings are milliseconds:

| Environment variable | Default |
| --- | --- |
| `MEMORY_ACTION_TIMEOUT_MS` | 20,000 mock; 180,000 live |
| `MEMORY_OLLAMA_TIMEOUT_MS` | 120,000; maximum 300,000 |
| `MEMORY_REPLY_TIMEOUT_MS` | mock: action timeout; live: greater of action timeout or Ollama timeout + 30,000 |
| `MEMORY_HTTP_TIMEOUT_MS` | 5,000 for audit/health/preflight requests |
| `MEMORY_STARTUP_TIMEOUT_MS` | 10,000 per isolated service |
| `MEMORY_EVIDENCE_TIMEOUT_MS` | 5,000 per diagnostic capture |
| `MEMORY_CLEANUP_TIMEOUT_MS` | 5,000 per close/termination stage |

The Ollama inference deadline includes response headers and the complete stream, rather than resetting each time a token arrives. It applies only to this test fixture's requests. Existing curator/Director budgets can cancel a request earlier. Test-local model presets allow the transport deadline to report before the surrounding generation budget; user presets and the Ollama service are untouched. The original bounded curator-setting/result polling counts and fall-through behavior are retained; exhausting those waits saves diagnostics without changing evaluation formulas.

Example:

```sh
MEMORY_ACTION_TIMEOUT_MS=30000 MEMORY_OLLAMA_TIMEOUT_MS=180000 \
MEMORY_REPORT=/tmp/memory-progress \
node tests/fork/intelligent-memory-browser.mjs --live
```

Failures/timeouts identify the failing browser step, arm, character and turn. Ollama timeouts also identify the inference request and originating browser step. `failure-*.json` contains bounded fixture stdout/stderr, browser errors, a small DOM/status snapshot and the last request/context/memory diagnostics. A token-masked screenshot is saved when a browser page is available. Captures have their own deadlines, so an unresponsive page/backend cannot indefinitely delay cleanup. Full network traces/DOM dumps are deliberately not recorded, since they could retain pairing credentials. Evidence file names are linked from `report.json` and progress output; a failure before Chromium starts naturally has no screenshot.

Cleanup closes the specifically launched Playwright browser server and waits for the UI/backend child processes created by this invocation. It escalates to killing only those owned handles if graceful shutdown times out, including on SIGINT/SIGTERM. It never searches for processes by name, kills a port owner, restarts a service or sends an unload/stop request to the user's Ollama service. No automatic fixture restart is added. Scenarios, synthetic messages, recall scoring and success formulas remain unchanged.

Follow-up verification: six Node tests exercise deadlines, interruption, credential redaction and owned-only cleanup; five Python tests exercise stalled headers/streams, stream preservation/metrics, cancellation and the authenticated fixture pipeline without external Ollama access. Mock residency checks also remain within the fixture instead of querying shared Ollama. Full browser acceptance remains blocked here by loopback `EPERM`; the smoke run confirms visible step reporting and JSON diagnostic capture for that failure, rather than claiming a browser pass.

## Navigation correction: hidden Character management at 1440 px

The saved A/B/C failures in `/tmp/f2841-browser/` all show Evelyn selected, observer connected, activity Ready, no JavaScript error, no open dialog and curator disabled. All three PNGs are **1440×1000**, matching the old runner viewport. `mountCompanion()` mounts Character management on `#character-panel`, not Chat. The real CSS hides that panel at widths up to 1499 px. Consequently `[data-menu-story]` exists inside a hidden ancestor; trying to click it cannot open curator controls. This was responsive navigation failure, not missing Ollama output or a closed curator accordion. The curator is currently a plain section inside the Story Memory drawer; the optional objective editor is a separate accordion.

The primary acceptance viewport is now **1920×1080**. `MEMORY_VIEWPORT_WIDTH` / `MEMORY_VIEWPORT_HEIGHT` allow responsive checks without changing timeouts. The navigation helper uses the actual Character/Chat view controls and scoped accessible drawer buttons. It opens Character first when hidden, opens Story Memory idempotently, scopes curator fields to that drawer, and restores Chat after reset/settings/diagnostics. Below 1500 px it closes the Character overlay before typing; on mobile it selects the Chat tab. It never forces hidden elements, rewrites application CSS or changes layout state through `evaluate()`.

A/B do **not** open curator controls: they verify the isolated backend reports curation disabled and fail if that is not true. C uses the real UI to enable curation and set eight turns, then verifies enabled/interval/timeout values through the fixture audit before the first conversation. All arms still use Story Memory for the required storyline reset and later memory inspection. Full conversation scenarios, models, synthetic prompts and all four scoring formulas remain unchanged.

Errors now distinguish missing, ambiguous, hidden, disabled and obstructed controls. Management diagnostics record actual viewport/breakpoint, dashboard view, target counts, dialog/disclosure state, computed display/visibility, dimensions and hidden ancestors. The helper does not confuse a hidden accessible role with an absent DOM element.

The initial `/ai/pair` **503 is separate**: the static UI probes optional desktop auto-pairing. `serve_local.py` returns 503 when its desktop pairing file is unset, unreadable or invalid. The manual test fixture creates no desktop pairing file; its subsequent explicit WebSocket authentication succeeded in all three captured runs. Manual submission disables further auto-pair attempts. The runner retains/logs this response rather than hiding it, and strips any inherited `EDGELOOP_PAIRING_FILE` from the test UI child so it cannot accidentally auto-pair with the user's real observer. A socket-free handler regression verifies the missing-file 503 behavior.

Run the turn-one gate first (Evelyn, all three arms, actual selected provider):

```sh
MEMORY_REPORT=/tmp/memory-turn1 node tests/fork/intelligent-memory-browser.mjs --live --setup-only
```

This mode records `setup_checks` with the reply, provider metrics, request count and latency, and has a separate `setup_completed` result. It does not claim recall acceptance or curator-generation quality after one turn. Then run the unchanged full comparison:

```sh
MEMORY_REPORT=/tmp/memory-full node tests/fork/intelligent-memory-browser.mjs --live
```

To repeat setup at the originally failing size:

```sh
MEMORY_VIEWPORT_WIDTH=1440 MEMORY_VIEWPORT_HEIGHT=1000 \
MEMORY_REPORT=/tmp/memory-turn1-responsive \
node tests/fork/intelligent-memory-browser.mjs --live --setup-only
```

The independent actual-DOM regression uses current `index.html`, layout/menu modules and CSS, synthetic presentation state, and no engine/backend/Ollama. It reproduces the old hidden-button click at 1440 px, tests navigation at 1920, 1440 and 390 px, C control interaction, return-to-Chat, idempotent drawer opening and missing/hidden diagnostics:

```sh
node tests/fork/memory-navigation-browser.mjs
```

Current verification: **568 Python tests pass (three existing socket cases deselected), 56 companion JavaScript tests pass**. Six navigation contract tests cover responsive routing, idempotence, missing/hidden elements and authoritative A/B/C configuration checks. The captured screenshots and source were inspected, but a fresh actual-DOM browser pass is environment-blocked: Chromium aborts during launch with `sandbox_host_linux.cc ... shutdown: Operation not permitted`. Mock setup cannot allocate loopback ports (`listen EPERM`); live setup and the full comparison stop at Ollama preflight (`connect EPERM 127.0.0.1:11435`). Thus **turn one and real recall results are not verified in this session**. Reports are in `/tmp/memory-navigation/`, `/tmp/memory-nav-setup/`, `/tmp/memory-nav-live-setup/` and `/tmp/memory-nav-live-full/`; the original user-captured evidence was not overwritten. No memory algorithm, model, product layout or active service changed.
