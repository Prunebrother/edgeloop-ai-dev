# F2.1 companion interface

F2 baseline: `e99ae3f`. F2.1 makes the companion the primary desktop experience while retaining original EdgeLoop control ownership. No F3 device commands, emotion classifier, new voice system, or generated character artwork are implemented.

## Layout and upstream boundary

`src/js/ai/layout.js` reparents the existing cockpit nodes after original listeners are installed. It preserves IDs, control state and event handlers. There are no cloned session controls or replacement calculations. The global Emergency stop button invokes the original Stop button, which uses the original immediate `stopSession` path. The observer never invokes that button. The original remote viewer/controller UI remains on its original layout.

At widths of at least 1500 CSS pixels, the default columns are 27% / remaining space (approximately 40%) / 33%. Labelled keyboard-accessible range controls adjust Session (23–34%) and Character (25–36%) widths. Minimum widths are 330 / 380 / 300 pixels; switching to two columns before those constraints cause overflow preserves readable controls. Width adjustments are per page and do not alter session settings.

At 761–1499 pixels, Session and Chat occupy the available width, and Character toggles a side panel. At 760 pixels and below, buttons select Session, Chat and Character views. Emergency stop and the original prioritised safety/disconnect banner stay available in every view. The banner is moved outside the panels and remains above the tablet artwork overlay. The session control dock and conversation composer stay outside their respective scrolling content. The heart-rate card remains sticky inside the session scroll area. Experience/goal controls, advanced session setup/sharing, output tuning/shortcuts and legal/about links remain accessible in groups. Native browser zoom is enabled.

`src/css/companion.css` is scoped to the companion shell; no transforms/zoom shrink the original dashboard. The only newly reviewed original-source change beyond F2 is an index stylesheet link and viewport accessibility update. The service worker precaches the public UI additions and retains AI/auth exclusions. The immutable upstream pin is unchanged; the reviewed-change manifest now identifies four original-source files, with 81 pinned files unchanged. `app.js` adds only the optional observation hook/refresher; engine, physiology, patterns, goals, calibration and drivers are byte-identical to the upstream pin.

## Acceptance follow-up: idle observation heartbeat

Live Mira acceptance exposed that original idle/paused sessions do not continuously call `syncTelemetry()`. The observer correctly expired the snapshot after five seconds and cancelled generation. The connection also wraps native browser timer functions, avoiding an illegal receiver when scheduling periodic sends/reconnects. The companion now requests a fresh allowlisted projection every second while authenticated, via a fail-isolated `syncAiObservation` callback. This does not tick the session, send peer telemetry, advance time, invent HR readings or dispatch hardware. Disconnected AI performs no periodic capture. Browser coverage verifies fresh observations through a pause longer than the lease while session seconds remain unchanged.

## Conversation and pairing

`companion.js` uses the existing `ReadOnlyConnection`, allowlisted capture, observer, Conversation Director, Modelfiles and per-model memory. Pairing uses the existing localhost `/observe` WebSocket, Origin checks and password field. The token is cleared immediately after submission, the setup form is hidden after authenticated readiness, and credentials are never persisted or placed in URLs. Automatic reconnect retains only the existing in-memory token. Disconnect clears it.

Model discovery is distinct from authenticated service readiness and telemetry freshness. Discovery/selection errors appear inline. Users explicitly select an installed model. Conversation uses safe text nodes, role-labelled bubbles, incremental deltas, multiline input, IME-safe Enter to send, Shift+Enter for newline, loading/error feedback and a generation-cancel button. History is bounded to 64 visible messages, retaining F2's client limit; switching models restores the backend-provided model history. Manual scrolling disables following until the reader returns near the bottom or presses Jump to latest. Chat scrolling does not scroll the session panel.

The sole new client-to-observer variant is `{version:1,type:"cancel_generation"}`. It clears pending AI events, interrupts the current generation and removes queued chats. It bypasses model discovery/selection work and never changes observations, session state, hardware or safety. Cancelled partial text remains visible until history is refreshed; it is not presented as a completed backend memory record. Existing safety observations can still independently interrupt generation.

## Artwork manifest and future state

`artwork-manifest.js` exports the twelve supported expression keys and an initially empty `MODEL_ARTWORK` manifest keyed by exact Ollama model identifiers, including tags. There is no built-in named character identity.

```js
'my-model:latest': {
  name: 'Character display name',
  artwork: '/src/assets/characters/my-character/default.webp',
  expressions: {
    neutral: '/src/assets/characters/my-character/neutral.png',
    happy: '/src/assets/characters/my-character/happy.webp'
  }
}
```

Add locally licensed artwork under `src/assets/characters/`; the static server allows public PNG/WebP/JPEG/SVG assets only in that subtree, with its existing traversal/symlink protections. Never place private data there. Supported states: neutral, happy, excited, playful, thoughtful, concerned, surprised, serious, amused, listening, speaking and relaxed.

`CharacterPresentation` is an independent presentation controller/renderer. `setModel(model)` resets to neutral; `setState({expression,activity})` accepts explicit presentation state. Requested artwork falls back to neutral, then model default, then the CSS placeholder. Failed image loads retry neutral and model default artwork in order, then restore the placeholder. The placeholder is hidden behind successful artwork so transparent assets have a clean background. Image-load revisions prevent stale loads from overwriting new model/expression choices. Images use `object-fit: contain`, preserving high-resolution portrait proportions and alpha transparency. Crossfades obey reduced-motion preference. Optional activity text accepts only listening/speaking.

A future backend extension can send a separately validated presentation-state event carrying model identity and an allowlisted expression. Its adapter should call this controller only for the selected model. No such event is accepted in the F2.1 wire protocol yet. Neither image loads nor expression mapping await or modify token delivery, session controls or telemetry. No physiological measurement is used to infer the user's emotional state. Modelfiles remain the authority for personality; no application personality prompts were added.

## Validation and evidence

Run:

```bash
python3 tools/fork_validate.py --tests --report /tmp/edgeloop-f21-upstream.json
node --test --test-isolation=none tests/fork/bridge.test.mjs tests/fork/presentation.test.mjs
PYTHONPATH="$PWD:/home/sean/projects/edgeloop-ai" /home/sean/projects/edgeloop-ai/.venv/bin/python -m pytest -q tests/fork
node tests/fork/browser.mjs
# With the local services already running and their pairing token:
EDGELOOP_ACCEPT_TOKEN=... node tests/fork/live-browser.mjs
```

The browser suite starts temporary loopback static/observer servers, uses the real observer/Director/memory with mocked Ollama transport, denies native device permission requests and intercepts Handy HTTP. It asserts no hardware request before explicit mock setup. It verifies that every original HTML element ID survives layout mounting, the original warning banner/dismiss listener, mode/goal listeners, Start/Pause/Resume/Stop, fresh telemetry, response streaming/cancel/scroll anchoring, multiline input, model memory isolation, continued session timing with AI disconnected, redacted credentials, compact pairing and portrait fallback.

Viewports: 1920×1080, 2560×1440, 1366×768, 768×1024, 390×844, 360×800 and pairing at 375×667. It checks horizontal overflow, composer visibility and accessible responsive views. Captures are visually inspected. Screenshots and machine report are in [screenshots/f2.1](screenshots/f2.1/); full generated output defaults to `/tmp/edgeloop-f21-browser` (override with `FORK_BROWSER_REPORT`).

Confirmed: 1057 upstream tests (32 files), 16 observer tests, nine JavaScript bridge/presentation tests, 221 preserved AI regression tests and original AI dashboard harness, plus Playwright. The sandbox Python run uses the established selector-polling wrapper; no assertions are skipped. Browser execution uses elevated host permissions for Chromium IPC and local fixtures. A follow-up real Mira smoke verified streamed dialogue reporting 98 simulated BPM, IDLE and zero elapsed seconds, with idle observations remaining fresh beyond the five-second lease. Broader dialogue quality, live Evelyn replies and physical hardware operation remain unverified. No real hardware was connected. The browser fixture terminates its servers at completion.
