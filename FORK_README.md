# EdgeLoop AI fork — F2.4

This is the primary application. Original EdgeLoop 1.1.3 owns every session,
physiological calculation, device operation and safety decision. The companion
is read-only: local Ollama chat, model-specific memory, a Conversation Director,
thinking controls and configurable character presentation in the three-column UI.
No F3 controls or new voice subsystem are implemented.

The Python backend is self-contained in `ai_observer/` and `companion_ai/`, with
its own `.venv` and declared dependencies. The legacy checkout is not needed.
See [architecture/migration](docs/fork/F22_CONSOLIDATION.md),
[developer workflow](docs/fork/DEVELOPMENT.md), [failure diagnosis](docs/fork/F22_CONNECTIVITY.md)
and [validation](docs/fork/validation-f22.json).

See [F2.4 character artwork and expressions](docs/fork/F24_CHARACTER_PRESENTATION.md),
[available/missing artwork](docs/fork/F24_ARTWORK_INVENTORY.md) and
[current validation](docs/fork/validation-f24.json). F2.3 telemetry-grounding
limitations remain documented; expression selection does not establish user emotion.

## Local development

```bash
./tools/setup-ai.sh                         # explicit dependency setup, once
./tools/serve-local.sh                      # UI: http://127.0.0.1:8770/
# In a second terminal:
./tools/serve-ai.sh --check                  # verify the configured existing Ollama
./tools/serve-ai.sh                         # observer: ws://127.0.0.1:8768/observe
```

Pair in Chat using the token printed by the observer, then select an installed
model and press Switch model. The token expires after one hour and is never
stored in browser storage. The observer WebSocket address is separate from the
Ollama HTTP endpoint displayed beneath the model picker.

`config/ai.toml` defaults to the existing character server at
`http://127.0.0.1:11435`. To use the older server explicitly:

```bash
EDGELOOP_OLLAMA_URL=http://127.0.0.1:11434 ./tools/serve-ai.sh
./tools/ollama-status.sh --url http://127.0.0.1:11435
```

No launcher starts Ollama, downloads/builds models, connects hardware or kills
an occupied port. Start an intended Ollama server manually only after checking
that port and its model directory. The main UI continues to operate when AI is
unavailable. Use the original manual HR simulator and mocked toys for acceptance;
HR simulation alone intentionally does not satisfy original toy readiness.

## Validation

```bash
python3 tools/fork_validate.py --tests --report /tmp/edgeloop-upstream.json
.venv/bin/python -m pytest -q
node --test --test-isolation=none tests/fork/bridge.test.mjs tests/fork/presentation.test.mjs
FORK_BROWSER_PORT=8780 FORK_OBSERVER_PORT=8788 node tests/fork/browser.mjs
```

The browser fixture denies native hardware permissions and mocks Handy/Ollama.
An explicit real-model smoke uses synthetic idle observations and an isolated
temporary data directory, with an already running local Ollama:

```bash
./tools/smoke-ai.sh --url http://127.0.0.1:11435 --models evelyn-lite-v1:latest \
  --thinking off --output /tmp/edgeloop-live-new.json
```

See LICENSE and [source attribution](NOTICE_FORK.md). The original upstream
history/pin and AGPL provenance are retained; model weights are not included.
