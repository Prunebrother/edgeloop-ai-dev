# F2.8.1 — Real-session reliability and narrative refinement

## Checkpoints and scope

Work continued directly on `experiment/ai-companion`, starting from clean HEAD `c3f8e33` (after `e508d5f` and the F2.8 checkpoint `c5bc599`). Initial implementation checkpoint: **`9c3f9fe492450a5c7688d46c519cae2ef9bb7224`**. Final implementation commit, including cancellation/fiction regressions: **`1c541e105922542c9fa3e7485f3c82de1799cf2f`**. Final checkpoint tag: **`f2.8.1-checkpoint`**. Resolve its exact documentation/evidence commit with `git rev-parse 'f2.8.1-checkpoint^{commit}'`; the annotated tag records validation limitations.

No branch/worktree, hardware test, model build, service restart or new inference process was created. Existing Celeste v1/v2 sources, artwork, installed models, private settings and conversation data were preserved. Original engine, drivers, safety thresholds, disconnect protection and command pathways are unchanged. The only additions inside the original app are optional read-only observations, guarded against exceptions, after existing operations, including reset cancellation. The reviewed upstream-file manifest and service-worker cache version are updated.

This checkpoint contains deterministic repairs. Live narrative quality and browser acceptance remain pending in an environment that can access localhost. It is not comprehensive physical-hardware validation.

## Completion investigation and repair

The label “The App Finished Me” does not identify one universal successful-completion event. Reading the original `cameEarlyBtn` handler, `beginSettle`, `finishSettle`, `restartSurvivalAfterOrgasm` and `stopSession` establishes these original semantics:

| Original branch | Accepted engine result | Companion meaning |
|---|---|---|
| Calibration, active, valid reading, confirmed dialog | Save original calibration setting; ease down then stop, or stop immediately | Accepted calibration completion; no physiological diagnosis |
| Survival, active, confirmed dialog | Ease down then restart the climb, or restart immediately; session counter continues | Accepted Survival completion/restart; not session termination |
| Other modes, confirmed accidental-release dialog | Increment learning-release counter; session-ending settle/stop | `came_early`: reported accidental release, not successful objective completion |
| Refused dialog, invalid/inapplicable calibration/Survival action | No accepted completion transition | No completion commentary |
| Stop, reset, protective pause | Original stop/reset/protection semantics | Never promote to successful completion |

Before this repair, the projection/protocol had only `came_early`; calibration and Survival completion were absent. `came_early` had a reactive lane, but still passed the shared session-detector commentary cooldown. Pending reactions could be cleared by stop handling before dispatch; an already generating Came Early response had an existing special preservation path. Stop also produced a deterministic notice and could subsequently queue an LLM stop reaction. Rejected/unchanged source events were not eligible for narration.

The exact missing reaction during the reported physical run **cannot be uniquely reconstructed**: no retained per-event generation trace or full recent conversation was available in the local observer data. The code paths above are reproduced by synthetic tests, not presented as a forensic reconstruction of that run. The prior F2.8 acceptance did not cover these combinations.

The repaired path is:

1. Original physical stopping remains first. `stopSession` makes a final optional observation after its existing motor-stop dispatch, before the original counter reset. Survival restart similarly projects its already accepted outcome. No click listener, controller or command is added.
2. The existing Capture projects allowlisted terminal reasons and emits `completion_accepted` for Calibration/Survival, retaining `came_early` for accidental release. The original reset snapshot follows separately. Terminal/following-reset observations flush immediately through the existing connection; the server's urgent gate admits them.
3. Strict protocol and BrowserObservation validate source session, sequence, source timestamp and mode/status/outcome evidence. Duplicate identities and unchanged terminal transitions cannot become new reactions.
4. Accepted completion/release is major, with its existing event identity. It bypasses spontaneous, reaction and detector commentary cooldowns. Proactive enablement, typing, busy-user generation, event freshness and scope restrictions still apply. A busy generation defers the event; it does not replace a user turn.
5. Stop preserves pending/in-flight completion/release while removing stale running/selection work. Ordinary stop/pause has one immediate deterministic notice and no second generated stop reaction. Safety notices remain immediate and independent of inference.
6. Context Compiler includes the triggering evidence and relevant objective/retained final facts. Model-native personality supplies the wording. Ollama retains `think: false`, the existing expression parser and existing bounded factual/repetition recovery. No new inference call was added.
7. Stop/reset acknowledgment carries `preserve_reaction` so the existing presentation controller does not cancel the eligible completion. New engine-session identity cancels/discards old generation. Source-state checks prevent a stale start/resume from becoming a fresh running claim.

The in-process end-to-end test covers accepted source completion → authenticated observer → major classification → scheduling → mocked Ollama → reset during generation → expression-bearing visible speech. It verifies exactly one ordinary inference request with thinking off and an acknowledged diagnostic result. Source projection and transport tests separately prove final-counter delivery before reset. These tests do not establish actual model prose quality.

## Completed-session facts

BrowserObservation retains at most **eight** immutable final summaries, exposing at most **three** to diagnostics and the latest relevant summary to compilation. Access is scoped to the provider/endpoint/model that observed termination. Switching models does not expose another model's completed-session facts; switching back restores its retained access. Retention is process-local, like the existing observer event buffer, and is not a new session controller or persistent conversation store.

A summary contains session identity, final verified active-running ticks when reliably captured, last observed ticks when partial, edge count, selected experience/goal, termination classification, source/receive timestamp, sensor/source availability, protective-state observation, bounded validated event references, and completeness/confidence. Physiological values are not invented or summarized by another model. `wall_clock_seconds` and `paused_seconds` remain null.

`active_running_seconds` is reliable only when a final pre-reset projection has a capture timestamp, follows a fresh observation and has nondecreasing source counters. Otherwise final duration is **unavailable**, with last verified ticks explicitly marked partial. A terminal marker attached to already reset zero counters cannot establish a zero-length session. No duration is inferred from conversation timestamps, reception age or sensor sample spans.

A later reset changes current `canonical_session.facts.seconds` to zero but cannot change the retained final summary. A new session cannot overwrite its predecessor's facts. Summaries older than 24 hours are marked stale historical records; they are never current telemetry. An observer restart loses this bounded buffer; the companion must then report unavailable final duration rather than reconstructing it from prose. Existing original EdgeLoop session-history saving is untouched.

Manual stops remain manual; the reset action now also projects its final counters after the original stop dispatch and is explicitly `cancelled`. Missing terminal metadata remains `cancelled_or_unclassified_stop`. If an unclassified stop follows protection, the summary says `stop_with_protection_observed`, without claiming the protection caused that stop. Accepted accidental release and calibration completion are separate classifications. A protective pause alone does not create a completed session.

## Objective creation and lifecycle

The supplied research-journal fixture failed **inside `NarrativeObjective` validation**, after the frontend's correct Create action and authenticated request payload. The old whole-object validator applied `OPERATIONAL` to every field. That regex matched benign words including `session`, `milestone` and `physiolog…`; a second filter also rejected `medical`, even in “without drawing medical conclusions.” The generic catch combined validation, lifecycle and disk errors into the reported unhelpful notice. No missing authentication/model identity or persistence failure was needed to reproduce this rejection.

Objectives now use field validators. Benign references to verified duration, pacing, milestones, voluntary feedback and nonmedical reflection are accepted. Explicit equipment commands, protection bypass, physiological targets/numerical BPM assertions and asserted medical conclusions are rejected with field-specific reasons. Objective text remains fallible fictional context and cannot supply telemetry evidence or commands. This is a narrow English pattern policy, not a semantic security classifier; read-only authority is enforced independently by the architecture.

Create requires a premise. Update is supported as an API alias for existing `revise`, and the UI labels it Update. Complete, Abandon, Pause and Resume retain existing lifecycle behavior. Unknown actions are request-schema errors; absent/terminal objectives and invalid lifecycle transitions have lifecycle errors. Validation errors identify fields; persistence errors have a separate code and preserve prior memory. Selected-model mismatch has its own explanatory response. Authentication and protocol errors remain at the existing boundary. Raw input, credentials and disk exception paths are not serialized.

Successful edits immediately publish refreshed `character_state`; the drawer displays the saved objective and correct action. Existing cancellation of queued/in-flight selected-model dialogue remains. Persistence is still explicitly opt-in through NarrativeMemory; restored objectives pause without granting narrative initiative. Reset/abandonment retains transcripts while fencing old narrative context. No automatic objective creation was added. User-described benign fictional plans can also be retained as ordinary fallible conversational excerpts without creating an objective. Relevant active journal objectives can support completion/reflection and timing turns, not just general story topics.

## Grounding, identity and conversation

The existing F2.3 canonical contract already distinguished current/stale facts, HR timestamps/source, simulated values, settings and unverified physical motion. The observed misleading language showed gaps in final factual checks rather than evidence that BLE-disconnect protection failed. The repair keeps that contract and adds narrowly targeted checks for:

- Assertions that disconnected/stale Polar/BLE sensors work normally, record or confirm measurements.
- Rising/falling heart-rate claims without a current physical measurement and matching validated trend; excitement reported by the user is not sensor evidence.
- Data proving physiological/medical/emotional outcomes.
- First-person future/completed real hardware claims, including “I'll adjust the stimulation transport accordingly.”
- Explicit previous-session numeric duration claims that conflict with retained final ticks or assert a duration when unavailable.

Suggestions that the user adjust controls, explicit fictional actions, subjective reports and uncertainty remain permissible. Explicit fictional physiology/motion and user-attributed pulse reports remain separate from sensor evidence. The new checks feed the existing bounded grounding correction mechanism; they do not add a second validator model or additional retry allowance. They are incomplete English regex checks, not proof that every accepted sentence is correct. Existing provisional user streaming can briefly expose a draft before the established repair/reset mechanism; event responses retain their validation hold.

Runtime guidance now explicitly separates character, participant addressed as “you,” and named third parties; it tells the model to keep its native role/voice on scientific topics, answer directly and allow goodbye/session conclusions without a new question. No character-specific generic personality templates or scripted responses were introduced.

Celeste v2's source is unambiguous: Ambassador Celeste Armand is an IRRA senior diplomat/Special Envoy; Laurent Armand is **her husband**, whom she still loves; the participant is separately described as an adult volunteer. Evelyn is Dr. Evelyn Voss at Asterion; Daisy Mae Harper runs Cloverfield. Their source references to one another are legitimate backstory, not in themselves cross-character leakage. No private recent transcript established the exact reported pronoun error's context, so truncation, contamination or a specific model mistake cannot be selected as its proven cause. The provider still prepends the exact selected model SYSTEM metadata. Tests verify native identity retention, relationship-source references, longer-context composition, model switching and per-model history/objective isolation. No Modelfile or installed model was altered.

Historical event records now retain event IDs. Compiler selection can exclude an already acknowledged event by identity instead of resurfacing it as fresh supporting evidence. Existing repetition/question scoring remains, with no new rewriting engine. Distinct voices, emotionally appropriate endings and long-term relationship reference resolution still need live human evaluation.

## Diagnostics

Existing Context Intelligence now includes compact event lifecycle and retained completed-session information. Event lifecycle records show ID, kind, session, monotonic sequence, source/receive timestamp and accepted/duplicate/wrong-session/stale/unproven decision. Existing Event Intelligence records retain a bounded sequence of scheduling stages: queued/deferred, dispatched, generation started, acknowledged, suppressed, failed or discarded. Identical repeated deferrals do not crowd out the important stages. Director diagnostics and existing compiler event/story references remain available. No tokens, credentials, private raw transcript or reasoning text was added to diagnostics.

## Validation

Final evidence is in [f281/validation.json](f281/validation.json) and [f281/upstream-tests.json](f281/upstream-tests.json).

- Python: **418 passed**, **3 deselected** because this sandbox denies actual socket creation. The excluded cases are occupied observer port, occupied UI port, and same-origin desktop HTTP pairing. They were attempted in the full run and failed/setup-errored with `PermissionError: [Errno 1] Operation not permitted`; no passing result is claimed for them. There are 46 new F2.8.1 cases. One existing Starlette TestClient deprecation warning remains.
- Companion JavaScript: **37 passed**, using `node --test --test-isolation=none --test-reporter=tap tests/fork/*.test.mjs`. Default Node subprocess isolation reports file counts here, so the explicit existing runner mode is required for individual case counts.
- Upstream: **1,057 passed, zero failed files** in the final per-file report. An initial all-files-in-one-process attempt had 1,055 passes and two storage-fixture failures caused by cross-file shared globals; the repository's `tools/fork_validate.py --tests` runner isolates files and is authoritative. Original engine/hardware sources were not edited to accommodate those tests.
- Browser: the Context Intelligence fixture was attempted and could not start its local server. Socket creation is independently confirmed denied. The seven baseline browser workflows (dashboard, character artwork, event reliability, narrative, character menus, Event Intelligence, Context Intelligence) are **unavailable**, not passed. Desktop-launcher browser checks share the same blocker. No screenshots or layout/portrait browser pass is claimed for F2.8.1.
- Live models: discovery at `http://127.0.0.1:11435` is inaccessible from this sandbox. Evelyn v1, Daisy v1 and Celeste v2 **were not live-evaluated** for F2.8.1. Earlier archived evaluations are not substituted for this milestone. No service was started/restarted or model evicted to work around it.
- Physical hardware: **not tested by Codex**. The reported real H10-disconnect stop is preserved as one user observation, not comprehensive validation.

The reproducible test-only selector shim is archived as [f281/sandbox-test-sitecustomize.py](f281/sandbox-test-sitecustomize.py); it is not loaded by the application. The sandbox also rejects writes to asyncio's Unix wake socket, making even an empty TestClient hang. In-process Python tests were run with a temporary `/tmp`-only `sitecustomize.py` that caps `EpollSelector.select` wait at 20 ms. This permits thread-scheduled in-process work to run; it does not enable TCP/HTTP or change application code. A pre-existing expiry test was made race-safe to consume already queued stale/cancellation notices before asserting WebSocket closure. The test still rejects any invented stop/success notice.

The additional essential grounding text is 704 characters, about **282 conservatively estimated tokens**. One ordinary composition measured 1,552 estimated prompt tokens excluding native identity, compiling in approximately 1 ms. This is a sample, not a latency benchmark. Actual prompt tokens, GPU usage, model latency and narrative quality could not be remeasured. Completed-session evidence is selected only when relevant; the latest summary is included rather than indiscriminately injecting the whole retained buffer. No new LLM call, output budget increase or resident LLM was added.

## Reproduce and activate

Outside the restricted sandbox:

```sh
cd /home/sean/projects/edgeloop-ai-fork
.venv/bin/python -m pytest -q tests/ai tests/fork
node --test --test-isolation=none --test-reporter=tap tests/fork/*.test.mjs
.venv/bin/python tools/fork_validate.py --tests --report /tmp/f281-upstream.json
CONTEXT_BROWSER_REPORT=/tmp/f281-context node tests/fork/context-intelligence-browser.mjs
```

Run the other six baseline browser scripts listed in F2.8 sequentially, because fixtures reuse ports. Use their isolated synthetic fixtures, never physical devices. With local Ollama available, evaluate all three named models sequentially with `think: false`: completion/accidental-release distinctions, retained-duration question, disconnected sensor, read-only authority, Celeste/Laurent versus participant references, direct questions and goodbye. A mocked model passing transport tests is not a substitute for reviewing those responses.

**Nothing was restarted during development.** At a convenient boundary after ending the physical session in the original UI, preserve any wanted nonpersistent conversation before manually activating the new observer. For the installed desktop service, restart **only** its observer:

```sh
systemctl --user restart edgeloop-ai-observer.service
```

Keep the existing Ollama and web services running. Reload `http://127.0.0.1:8770/`; the existing desktop pairing route reads the refreshed private pairing file. Do not copy its credentials into reports. If running the observer manually instead, stop only that observer's terminal process and run `./tools/serve-ai.sh` from the repository; use the new process's local pairing flow. No model rebuild, new model or full-stack Stop/Start is required.
