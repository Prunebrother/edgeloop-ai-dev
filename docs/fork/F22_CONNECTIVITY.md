# F2.2 connectivity repair checkpoint

Pre-change fork: `965727f` (includes F2.1 plus idle heartbeat and thinking controls). Legacy committed code: `9e89fa1`, with a modified Evelyn Modelfile and untracked character-development assets/tools. Legacy files are not modified. Backups are under `/home/sean/Work/backups/edgeloop-f22-20261027`, including both Git bundles, a source/working-file archive excluding model weights/environments, working diff and hashes. Fork-only backup references preserve both tips.

## Reproduced failures

The observer already reads `EDGELOOP_OLLAMA_URL` directly when constructing `ModelManager`. An isolated browser/backend run with the variable set to port 11435 confirmed that the manager receives that origin. The provider uses the origin for `/api/tags`, `/api/show`, `/api/ps` and `/api/chat`; it does not hardcode 11434 after construction. Shell environment changes do not reconfigure an already running process. The old launcher implicitly selected the legacy virtual environment and package through PYTHONPATH, obscuring which code/configuration was running.

At the start of this task the host had listeners on 8770 and 11434, but no observer on 8768 and no Ollama listener on 11435. A direct 11435 discovery request was refused. This is the observed runtime state, rather than an assumption that an environment override was ignored. The character-development notes also record that their temporary 11435 runtime was stopped after earlier tests. No server has been stopped or models deleted by this repair.

With discovery intentionally unavailable, the original browser displayed `Local model discovery unavailable` / `Ollama request unavailable`, retained a default option with value `No models loaded`, and left Switch model enabled. Clicking it sent exactly:

```json
{"version":1,"type":"select_model","selection":{"model":"No models loaded"}}
```

The closed schema correctly rejected this at `select_model.selection.model` with `string_pattern_mismatch` (spaces violate the model identifier pattern). It returned the separate `Invalid read-only message` error. This is a reproduced path producing the reported errors, not a claim that historical frames that were never logged have been recovered. See [reproduction evidence](f22/failure-reproduction.json).

## Repair

Discovery placeholders now have empty, disabled values. Selection is enabled only for identifiers from successful discovery, and a second send guard prevents programmatic placeholder submissions. Failed discovery clears the selectable names. The UI distinguishes the observer WebSocket from the backend-configured Ollama HTTP origin and displays that origin. Model discovery failures identify the unavailable endpoint.

Validation remains strict. Rejections now return/log only field paths and error codes, never raw messages, chat, credentials or Pydantic input values. Invalid fields, commands and authentication/origin restrictions are unchanged.

`config/ai.toml` defaults to the existing character endpoint `http://127.0.0.1:11435`; `EDGELOOP_OLLAMA_URL` overrides it. Loopback-only HTTP origins are validated. There is no silent fallback to the legacy server or automatic Ollama startup. `python -m ai_observer.server --check` prints the resolved endpoint and tests discovery. `EDGELOOP_OBSERVER_PORT` selects the observer port; occupied ports produce an actionable error and never kill a process.

## Checkpoint validation

21 observer tests pass; browser acceptance passes on isolated ports 8780/8788, including the unavailable-Ollama placeholder regression, thinking controls, session lifecycle, telemetry and responsive layouts. Model discovery against real 11435 awaits that existing server being available; no model weights were copied or rebuilt. Consolidation is the next checkpoint.
