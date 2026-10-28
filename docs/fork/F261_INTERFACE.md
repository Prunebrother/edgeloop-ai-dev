# F2.6.1 — Director and Story Memory interface

Baseline: `3293d6a` (`f2.6-checkpoint`), clean `experiment/ai-companion` branch. Recovery branch: `backup/f261-before-3293d6a`. Existing artwork, model definitions/stores, original engine/control handlers, hardware drivers and safety logic were preserved.

The character panel now has a compact **Director / Story Memory** toolbar beneath the name, expression and activity indicator. Story controls were removed from beneath the chat composer. A collapsed premise/phase summary appears only when actual story memory has a premise; it can show the latest significant verified event. No storyline title is inferred from telemetry. Portraits retain their high-resolution assets, aspect ratio, expression fallbacks, transitions and caching; menu interaction retains the existing image node.

## Menus and validated backend state

Both menus are nonmodal drawers confined to the character panel. Opening one focuses its close button; Escape closes it and restores focus to the toolbar. Clicking outside closes it without swallowing the underlying action. Keyboard focus may leave the drawer intentionally, allowing access to global emergency and original session controls. Drawers scroll internally on mobile/tablet and never make the surrounding application inert. Character identity, expression and activity remain visible above an open drawer.

Director separates an **editable, service-wide proactive dialogue toggle** from read-only diagnostics: Director status, initiative policy, latest same-session significant verified event/significance/age, last decision, global/reaction cooldowns, pending commentary, tracked suppression count and active response source. Frequency cooldowns are pacing constraints, not scheduled-response promises. Only existing `spontaneous_enabled` behavior is editable; no BPM event detector or hardware controls were added. Strict Pydantic validation rejects non-Boolean settings and extra fields. The backend saves the complete existing Director config atomically to its existing private `director.json` before acknowledging success. Disabling proactive dialogue cancels only an active unsolicited response, clears pending commentary and prevents newly received events from queuing for later replay; user chat and deterministic safety notices remain independent.

Authenticated WebSocket messages reuse the current origin/token/owner checks:

- `get_character_state` with the selected `model`: obtains the bounded presentation-safe view, without inference.
- `configure_director` with Boolean `proactive_enabled`: validates and persists the existing setting. Only a successful save acknowledgement updates the displayed saved status.
- `reset_narrative` with selected `model`: reuses the existing reset. Legacy omitted-model requests remain compatible; new UI requests always carry model identity, and stale-model requests are rejected.

Views refresh after accepted dialogue/reset and every two seconds while a drawer is open. Closed menus do not poll. Unsaved settings and story text selection survive passive refreshes. Disconnection/model switching clears stale menu state; replies for another model are ignored. Public UI state excludes credentials, internal reasoning and raw configuration/storage dumps.

Story Memory renders the current premise, advisory phase, all bounded developments/choices/commitments, unresolved thread and recent update excerpts as labeled sections with honest empty states. It identifies the selected model and explicitly distinguishes fallible fictional/conversational excerpts from authoritative EdgeLoop facts. It adds no summarizer call and no personality instructions.

## Start New Storyline semantics

**Start New Storyline** opens an explicit inline confirmation. **Keep current storyline**, Escape or closing the drawer leaves state intact. Confirmation then:

1. Cancels active generation and drops queued pre-reset chat/pending commentary.
2. Resets only the selected provider/endpoint/model’s narrative state and generates a fresh random narrative epoch.
3. Clears that scope’s Director topic/questions/repetition/event-response context.
4. Excludes pre-epoch dialogue from subsequent model requests, including history restoration and model switching. Existing transcript records remain visible/stored within the existing bounded-memory policy; no conversation-clearing action was added.
5. Leaves canonical session observations, verified event history, operational state and other models’ story memory intact.

Completed dialogue records now carry their narrative epoch. Generation checks include model, session and narrative epoch in addition to the existing cancellation generation. An old response cannot restore the abandoned story even if a provider ignores cancellation. The reset boundary is saved using the existing narrative SettingsStore record even when optional cross-session story persistence is OFF, so a backend restart cannot reintroduce pre-reset persisted chat. This stores an empty boundary record, not physiological history or automatic story persistence. Later story excerpts retain the existing persistence opt-in. Source telemetry remains authoritative and independent of narrative filtering. The model may coincidentally invent similar fictional details; the guarantee concerns exclusion of abandoned context, not semantic control of free-form model output.

## Validation and evidence

[Results](validation-f261.json) and [screenshots/reports](f261/) record:

- **1,057 upstream**, **272 Python**, **30 bridge/presentation** tests passed. The final upstream pin was checked after backend/UI changes; reviewed original-file change is only the service-worker module precache/cache version. One existing FastAPI/Starlette deprecation warning remains.
- Existing dashboard, all-expression artwork and original-control event Playwright suites passed. Both characters, all 24 portraits, missing-image fallbacks, reduced motion, streaming, model memory, simulator milestones, accepted/rejected Came Early, cancellation/disconnection and original Stop were exercised using simulated HR and intercepted device HTTP only.
- Updated narrative browser acceptance and focused character-menu acceptance passed: menu open/close, keyboard focus/Escape, readable story view, cancel/confirm reset, retained transcript, old-story exclusion in actual outbound mocked Ollama payloads, model isolation/restoration, reset during streaming, saved toggle restoration, unsaved edits during polling, verified goal/significance display, no disabled-event replay and no menu-induced inference.
- Screenshots cover 1920×1080, 2560×1440, 1366×768 and 390px mobile. Desktop and mobile images were visually reviewed. Emergency controls remain visible and interactive; the composer stays in Chat. These are mocked-model UI screenshots, not evidence of improved narrative quality. F2.6 model-quality limitations and deferred full manual user acceptance remain unchanged.
- Thinking OFF is enforced by the unchanged shared Ollama transport and existing/new outbound-payload tests. No inference call was added for menus, settings, reset or narrative display. No Ollama server was stopped/restarted and no installed model was modified.

Reproduce with:

```sh
.venv/bin/python -m pytest -q tests/ai tests/fork
node --test tests/fork/bridge.test.mjs tests/fork/presentation.test.mjs
.venv/bin/python tools/fork_validate.py --tests --report /tmp/f261-upstream.json
FORK_BROWSER_PORT=8840 FORK_OBSERVER_PORT=8848 FORK_BROWSER_REPORT=/tmp/f261-dashboard node tests/fork/browser.mjs
CHARACTER_BROWSER_REPORT=/tmp/f261-artwork node tests/fork/character-browser.mjs
EVENT_BROWSER_REPORT=/tmp/f261-events node tests/fork/event-reliability.mjs
NARRATIVE_BROWSER_REPORT=/tmp/f261-narrative node tests/fork/narrative-browser.mjs
NARRATIVE_BROWSER_REPORT=/tmp/f261-menus node tests/fork/character-menus-browser.mjs
```

The last two fixtures share ports 8850/8858; run them sequentially. Tests use isolated temporary settings/history and do not change the running user service. The running companion observer was deliberately left intact to preserve any in-memory user conversation. Restart only that companion service and reload the browser to activate the new backend/UI; restarting produces a fresh pairing key. EdgeLoop and Ollama need no restart. Do not enable proactive dialogue merely by switching models: the persisted setting is service-wide.
