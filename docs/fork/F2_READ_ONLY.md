> **F2.2 update:** The fork now includes its own companion package and venv. References below to legacy runtime imports are historical. See [current architecture](F22_CONSOLIDATION.md) and [development](DEVELOPMENT.md).

> **F2.1 update:** The original optional panel is now the integrated companion dashboard. See [F2.1 interface, cancellation and browser evidence](F2_1_INTERFACE.md). Earlier browser-block notes below are historical. The read-only trust boundary remains in force.

# F2 read-only companion integration

The F2 implementation reuses the AI code at `/home/sean/projects/edgeloop-ai/` (baseline `9e89fa1`). It never imports that project's `app`, `session`, `session_bridge`, `core` or `demo` modules. No Node coordinator, motor sink, browser-controller callback or AI tool executor is created. Source/model data from the existing project is preserved. F1 is backed up locally by tag `backup/f1-e651754`.

## Launch both components

Normal host terminal 1:

```bash
cd /home/sean/projects/edgeloop-ai-fork
./tools/serve-local.sh
```

Normal host terminal 2:

```bash
cd /home/sean/projects/edgeloop-ai-fork
./tools/serve-ai.sh
```

Open **http://127.0.0.1:8770/**. Both servers bind **127.0.0.1 only**; neither installs a system service, starts Ollama, pairs a device or starts a session. The service is at `ws://127.0.0.1:8768/observe`. Start Ollama separately if real-model dialogue is desired. `EDGELOOP_AI_SOURCE` can locate the existing AI checkout/virtualenv on another host; its existing Python dependencies are reused.

The observer prints a random pairing token in its terminal. Open **Optional local AI companion · read-only**, paste the token, click **Enable AI connection**, choose an installed model and click **Switch model**. Send a normal question such as “What is the current BPM and session mode?” Only a successfully selected model can answer; no simulator identity is substituted on the normal service path. The token input is cleared after enabling, and no token enters URLs/localStorage. **Disable AI** closes only this bridge.

Use original manual controls and original simulated HR. In this phase use fake/mocked devices only. The original full-session readiness check still requires a toy; the browser test provides a mock Handy API. Do not use real credentials or grant device permissions during the experiment. The page remains the original EdgeLoop interface with one initially collapsed companion panel; all session controls retain their original handlers.

Personal companion data defaults to `.ai-data/` in this checkout and can be relocated with `EDGELOOP_FORK_AI_DATA`. The static launcher serves only public application assets; AI memory, `.git`, Python files, node_modules, directory listings, traversal and symlink aliases are excluded. Data/caches are Git-ignored. No existing data is automatically copied or migrated. Model-specific history is retained across switches by the existing service; cross-service-restart persistence follows its existing `memory-config.json` setting. Inference presets retain the existing `model-presets.json` format. Existing capability/context/thinking checks still apply to installed models.

## Original integration seam and ownership

`app.js:syncTelemetry()` passes source state and device booleans to an optional hook. The hook is lazy-loaded after original boot and wrapped so its absence/failure cannot interrupt original telemetry or controls. `Capture` explicitly projects public values; the existing WebRTC telemetry payload is never forwarded (it includes Mystery targets/history). The original engine, rules, patterns, clock, calibration, goals and drivers are unchanged.

The projection includes browser-generated session identity, original status/seconds, experience/active mode/goal, measured HR, engine-effective maximum/pullback, edge count, displayed intensity, primary/secondary output and stroke range, device/readiness booleans, signal/contact/watchdog flags and constrained fault enums. No names, keys, raw history, arbitrary configuration, hidden targets or free-form telemetry instructions are accepted. A small local trend window describes new measured readings; it expires and never changes physiological values or motor output.

Snapshot events are semantic transitions: start/pause/resume/stop, mode/goal change, edge, signal/contact/device changes and five-minute milestones. No event is created merely because another measurement arrives. Disconnected periods retain only the newest state; their old events are discarded. Session identity changes on a new original run, not on model selection or AI reconnect.

## Shared AI modules and compatibility adaptation

`ModelManager`, `ConversationService`, `ConversationDirector`, Ollama providers, context budgeting, model memory and diagnostics come directly from the existing package. The new factory is necessary because the old default app creates a competing B2a controller. The new server contains only authentication, bounded transport and routing to those shared classes.

The shared Director filters a legacy flat session schema. `ObserverDirector` changes only its context projection to preserve the validated nested original-state snapshot and freshness/source flags. Scheduling, event aggregation/dedup, repetition handling, topic state and memory remain shared. The existing provider preserves the selected Modelfile's embedded system content alongside neutral runtime context. No character selector/profile/personality instructions are added.

F2 deliberately sets event responses **off**. Semantic events still reach the Director and subsequent user dialogue, but periodic telemetry never requests an unsolicited model turn. Safety observations can cancel obsolete commentary and emit deterministic notices only when the browser actually reports paused/stopped state. An AI disconnect emits cancellation/freshness changes, not an invented device stop. Read-only model text—including JSON-shaped “commands”—is displayed with `textContent`; native tool calls are rejected by the shared text-only provider path. No execution acknowledgement is claimed: the panel explicitly says F2 has no control requests.

## Security and protocol v1

- WebSocket-only private API; HTTP exposes minimal health information. Exact allowed browser origins are `http://127.0.0.1:8770` and `http://localhost:8770`; Host is restricted. HTTP does not grant cross-origin access, and WebSocket Origin is checked before accepting. Ollama is never exposed through a browser proxy.
- A strict first `auth` frame must arrive within five seconds. The 32–128 character token is compared in constant time, remains in memory, expires one hour after service creation and is revoked by restart. One browser owns observation at a time; another browser is rejected. Same-browser reconnect replaces the previous connection and cancels stale generation.
- Each connection receives a new epoch. Observation sequence must increase; old epochs and remembered retired session identities are rejected. Event IDs are deduplicated with a bounded 256-entry/five-minute cache; session identities retain a bounded 64-entry retirement list. No old observation/event batch is replayed after reconnect.
- Incoming frames are limited to 16 KiB; output to 64 KiB. Browser output is one latest snapshot plus at most 16 coalesced events, normally one frame/second. Pause/stop/signal-loss transitions flush promptly and bypass ordinary observation rate limiting. Browser network backpressure closes/reconnects instead of accumulating old state.
- Server presentation queue: 32 messages; AI-work queue: eight; shared Director pending events: eight. Slow consumers must resync. Model operations run separately from observation receipt, so switching/loading a model cannot hold up stop observations or session telemetry. Chats have a 12/minute limit.
- Schemas forbid unknown keys and unrestricted telemetry strings. The only application input variants are observations, list models, select model and chat. No `control`, approval, session-start, hardware, configuration, calibration, reset, Came Early or Force Orgasm endpoint exists. No executor is attached.
- The service worker bypasses the local AI service/private AI paths. Tokens, chats and auth replies never enter URL caches. Text streaming and selected-model history are presentation only. Production source is available in this repository plus the identified existing AGPL AI dependency; retain both when distributing.

The observer never increments session time, recalculates ceilings or scales movement. After five seconds without observation—or on disconnect—AI context is explicitly unavailable. Last-reported values are retained diagnostically without claiming they are current or that a physical device stopped. This is an observation lease, not a controller or hardware lease.

## Validation and remaining acceptance

Automated validation: **15 observer/protocol integration tests**, **seven JavaScript adapter tests**, **1057 upstream tests**, **221 existing AI regression tests**, and the existing dashboard DOM harness pass. Tests cover model-neutral untrusted context, native/JSON command rejection, model memory isolation, observation continuity during a slow switch, safety cancellation, missing/expired auth, exact origins, bounds, sequence/epoch/session replay, source redaction, static private-data isolation and disconnect behavior.

`tests/fork/browser.mjs` exercises original UI/manual HR, a mocked Handy, contextual streamed responses using mocked Ollama, a model switch during a live original session, AI shutdown and original Stop. It uses fresh browser storage and denies BLE/serial/microphone permissions. The actual sandbox attempt is **blocked at Chromium startup** (`Operation not permitted`); no browser/E2E pass or real-model response is claimed. Original F1 host UI acceptance remains outstanding. No actual hardware was connected.

Host commands:

```bash
# Existing AI dependencies + both source packages:
PYTHONPATH="$PWD:/home/sean/projects/edgeloop-ai" /home/sean/projects/edgeloop-ai/.venv/bin/python -m pytest -q tests/fork
node --test --test-isolation=none tests/fork/bridge.test.mjs
python3 tools/fork_validate.py --tests --report /tmp/fork-upstream.json
node tests/fork/browser.mjs
```

The in-process tests in this sandbox use the existing 10 ms selector-polling workaround for restricted TestClient wakeups; no assertions are skipped. The Playwright browser and all loopback services require an unrestricted host. The browser fixture uses ports 8770/8768 and requires them to be free. Its Ollama transport is mocked, so its pass would not replace a live Evelyn/Daisy/Mira acceptance run.

## F3 gate

F3 has not begun. Before enabling bidirectional requests, finish host browser acceptance and live-model questions about changing original state; inspect Director silence/event behavior and model-switch continuity. Preserve F2's no-controller import test. Then design explicit manual/assisted authorization, a simulation-only device boundary, original-controller high-level routing, deadline/identity/dedup safety checks, user-stop precedence and requested/accepted/applied/rejected/unconfirmed acknowledgements. Credentials, configuration/calibration/safety resets, new-session start and special actions remain excluded. Validate these before any F3 claim; physical-device control and safety verification remain later work.
