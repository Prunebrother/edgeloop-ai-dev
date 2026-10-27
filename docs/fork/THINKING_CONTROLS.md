# Companion thinking and activity controls

Evelyn and Mira were configured with `thinking: true` during initial live acceptance. The UI now exposes that backend-confirmed setting beneath the model picker.

## Use

Pair, select a model, then press **Thinking: On/Off**. A change is applied immediately through authenticated model selection, and the button updates only after backend acknowledgement. Model operations are serialized and the control is disabled while a reply/settings change is in progress. Cancel a reply before changing its mode. The preference is saved per model using the existing model presets. Switching thinking modes preserves the selected model's conversation memory and the visible chat/scroll position.

Models without advertised thinking support select with thinking off and display **Thinking unavailable**. An explicit attempt to enable unsupported thinking is rejected without changing the usable selection. Failed settings requests restore the previously confirmed mode.

## Status feedback

- **Offline**: no authenticated observer connection.
- **Select a model**: paired, but no model activated in this browser.
- **Applying model…**: awaiting confirmation of selection/settings.
- **Ready**, green: model selection is confirmed and chat is available.
- **Working · thinking on/off**, pulsing purple: a request is pending or generating before visible answer tokens.
- **Responding**, pulsing purple: visible answer tokens are arriving.
- Errors appear inline, with a failure badge; cancellation/completion restores Ready.

Ready means a confirmed usable selection, not a claim that Ollama currently holds the model in GPU memory. Ollama loads lazily and can unload idle models. Working can include loading, prompt processing and reasoning; it does not infer or expose internal reasoning tokens. Motion respects reduced-motion preferences, state is announced accessibly, and color is accompanied by text.

## Protocol and isolation

`select_model` adds one optional strictly typed `thinking` boolean, outside the existing shared `selection` object. Omitted values preserve per-model settings; unsupported models default to false. The observer checks capabilities and uses existing `AIConfig` / `ModelManager.select`, returning `thinking` and `supports_thinking` in `model_selected`. The existing Ollama provider sends native `think: true/false`; no personality or reasoning instructions are inserted into prompts. No backend package, engine, telemetry projection or device control path is changed.

## Validation

18 observer tests pass, including native provider request flags, per-model persistence, retained memory/observation, strict boolean validation and unsupported-model rollback. Nine JavaScript bridge/presentation tests pass. The expanded Chromium fixture verifies On/Off confirmation, inference flags, unchanged chat history, Ready/Responding indicators, generation locking/cancellation and all prior responsive/session/telemetry checks. Browser fixtures support separate loopback ports to avoid interrupting a user's running services:

```bash
FORK_BROWSER_PORT=8780 FORK_OBSERVER_PORT=8788 FORK_BROWSER_REPORT=/tmp/edgeloop-thinking-browser node tests/fork/browser.mjs
```

Screenshots and the browser report are in [screenshots/thinking-controls](screenshots/thinking-controls/). The screenshot review covers desktop and mobile. Real hardware remains disconnected. The previously recorded upstream and shared-AI regressions are unchanged baselines; this change reruns the observer, bridge/presentation and browser suites.
