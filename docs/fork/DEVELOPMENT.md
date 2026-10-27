# Developing the consolidated EdgeLoop companion

The fork is authoritative. Do not run the legacy `edgeloop_ai.app` alongside it;
that application owns a different session/controller. No legacy checkout, venv,
PYTHONPATH or copied model store is needed by this fork.

## Setup and launch

```bash
cd /home/sean/projects/edgeloop-ai-fork
./tools/setup-ai.sh
./tools/serve-local.sh
```

The UI is `http://127.0.0.1:8770/`. In another terminal:

```bash
cd /home/sean/projects/edgeloop-ai-fork
./tools/serve-ai.sh --check
./tools/serve-ai.sh
```

The observer prints the configured Ollama origin and a random one-hour pairing
token. In Chat, leave the companion WebSocket at `ws://127.0.0.1:8768/observe`,
paste the token, pair, then select a model and press Switch model. The HTTP Ollama
origin is not the companion WebSocket address. Tokens are cleared from the form,
kept only in memory for reconnect and never put in URLs or browser storage.

`setup-ai.sh` creates this checkout's `.venv`, installs pinned requirements and
installs the local package editable. It starts no service. For an existing offline
wheel cache, equivalent setup is `pip install --no-index --find-links /path/to/wheels
-r requirements.lock`, then `pip install --no-build-isolation --no-deps -e .` in
that venv with setuptools installed. Do not reuse the legacy venv as a shortcut.

## Select and inspect an existing Ollama server

The default in `config/ai.toml` is `http://127.0.0.1:11435`. An environment override
wins over TOML:

```bash
EDGELOOP_OLLAMA_URL=http://127.0.0.1:11434 ./tools/serve-ai.sh --check
EDGELOOP_OLLAMA_URL=http://127.0.0.1:11434 ./tools/serve-ai.sh
# Or point EDGELOOP_AI_CONFIG at another TOML file with [ollama] url = "...".
```

Restart the observer after changing its origin; environment changes do not affect
an existing process. A restart changes its pairing token and clears non-persisted
in-memory chat. The original browser session and hardware safety remain independent.
Set `EDGELOOP_OBSERVER_PORT` to choose another observer port, then update the UI's
WebSocket field. The allowed browser origins remain exactly localhost/127.0.0.1
on UI port 8770; other UI origins require an explicit reviewed configuration, not
a wildcard. `EDGELOOP_FORK_AI_DATA` relocates private companion settings/history.

```bash
./tools/ollama-status.sh --url http://127.0.0.1:11434
./tools/ollama-status.sh --url http://127.0.0.1:11435
ss -ltnp
```

The diagnostics list API model names/version and, where permitted on Linux, only
the matching Ollama process's PID and OLLAMA_MODELS. The API does not expose its
model directory, so the process environment is checked separately. It never dumps
other environment variables or credentials. Known stores on this host:

| Port | Intended model store | Installed manifest count at F2.2 |
|---|---|---|
| 11434 | `/home/sean/projects/edgeloop-ai/.ollama/models` | 3 |
| 11435 | `/home/sean/.ollama/models` | 17 |

If the intended 11435 runtime is stopped, an operator can start that existing store
manually after confirming the port is free:

```bash
OLLAMA_HOST=127.0.0.1:11435 OLLAMA_MODELS=/home/sean/.ollama/models \
  OLLAMA_NUM_PARALLEL=1 OLLAMA_MAX_LOADED_MODELS=1 OLLAMA_FLASH_ATTENTION=1 ollama serve
```

This is an explicit operator command, never a launcher side effect. Do not start a
second process on an occupied port, stop an unrelated process, move weights, or
recreate an installed tag to repair connectivity. An unavailable configured server
produces a clear discovery error; it does not select another server automatically.

## Character development

Source definitions are in `characters/models/`; retained generated definitions are
in `characters/build/generated/`, with the preserved lite-v1 definition in `archive/`.
Hashes and original paths are in `f22/migration-sources.json`. The historical lite
experiment notes/evidence are retained separately, including the decision not to
promote the candidate. Modelfile content was not edited during consolidation.

```bash
.venv/bin/python tools/characters/build_character.py --help
.venv/bin/python tools/characters/build_character_v11.py --help
.venv/bin/python tools/characters/compare_evelyn_lite.py --help
```

Builders use central TOML/environment endpoint configuration and require an explicit
`--create` before invoking Ollama create. No builder/create/pull was executed for
F2.2. Future model changes require deliberate approval; changing model personality
belongs in source Modelfiles, never in an application persona prompt. Update exact
identifier-to-artwork associations in `src/js/ai/artwork-manifest.js` after adding a
model. No artwork was generated here.

## Tests and real-model smoke

```bash
python3 tools/fork_validate.py --tests --report /tmp/edgeloop-upstream.json
.venv/bin/python -m pytest -q
node --test --test-isolation=none tests/fork/bridge.test.mjs tests/fork/presentation.test.mjs
FORK_BROWSER_PORT=8780 FORK_OBSERVER_PORT=8788 \
  FORK_BROWSER_REPORT=/tmp/edgeloop-browser node tests/fork/browser.mjs
```

Install Playwright/Chromium locally if not present; the original package manifest
is unchanged. Browser fixtures use separate ports, temporary AI data, an inventory
fixture of 17 character names, mocked Handy/Ollama and denied device permissions.
No physical hardware is required or permitted for these automated tests.

The explicit smoke below uses the real observer protocol and existing configured
Ollama, a temporary data directory, synthetic IDLE/98 BPM observations, native
streaming, exact system metadata hashes and model-specific memory restoration.
It creates no network listener or Ollama server and never invokes a driver.

```bash
./tools/smoke-ai.sh --url http://127.0.0.1:11435 \
  --models evelyn-lite-v1:latest evelyn-qwen35-stable:latest \
  --thinking off --max-tokens 160 --output /tmp/edgeloop-smoke-new.json
```

Use a new output path on each run. `--thinking on` is explicit; small output budgets
may be consumed by reasoning before any answer. Raw reasoning is counted, not saved.
A transport pass does not establish character quality; reported factual accuracy
is recorded separately. No model is recreated or silently substituted. The browser
can also use an already running observer through `tests/fork/live-browser.mjs` with
`EDGELOOP_ACCEPT_TOKEN`, `EDGELOOP_ACCEPT_MODEL`, `LIVE_BROWSER_URL`,
`LIVE_OBSERVER_URL` and `LIVE_BROWSER_REPORT` environment variables. Real smoke
is limited by the configured server's actual availability.

The original 221-test legacy suite and old dashboard harness were run read-only for
migration evidence. Ongoing fork development uses its owned Python tests and current
browser harness, rather than importing or duplicating that old application.

## Full opt-in live character acceptance

With the existing 11435 server running and configured for one loaded model, run:

```bash
EDGELOOP_LIVE_ACCEPTANCE=1 LIVE_ACCEPTANCE_REPORT=/tmp/edgeloop-live-new-run \
  node tests/fork/live-acceptance.mjs
```

This starts isolated UI/observer fixtures on free ports 8780/8788, performs real
sequential inference for Evelyn Lite v1, Evelyn Qwen3.5 Stable and Daisy Qwen3.5,
monitors global/runner VRAM, verifies per-model memory and interrupts only a test
inference socket. Session devices are mocked. No Ollama daemon or normal user
observer is started/stopped. Use a new report directory each time. See
[F2.2 live results and limitations](F22_LIVE_VALIDATION.md).

## F2.3 telemetry grounding validation

The [canonical contract](SESSION_DATA_CONTRACT.md) defines source/freshness rules.
The reusable twenty-case corpus is `tests/fork/grounding_cases.py`. Tests instantiate
no hardware or second session engine. Run from the fork:

```bash
.venv/bin/python -m pytest -q
node --test --test-isolation=none tests/fork/bridge.test.mjs tests/fork/presentation.test.mjs
FORK_BROWSER_PORT=8780 FORK_OBSERVER_PORT=8788 \
  FORK_BROWSER_REPORT=/tmp/f23-browser node tests/fork/browser.mjs
.venv/bin/python -m tests.fork.evaluate_grounding --live \
  --output /tmp/f23-eval-new-directory
```

The live evaluation requires the already-running 11435 server, one loaded model/
parallel request, nvidia-smi and the existing fork environment. It never starts or
restarts Ollama, invokes a device API, changes a Modelfile or copies weights.
Requests run sequentially with matched input snapshots/questions/history and the
same model's embedded SYSTEM. The comparator loads only the pinned F2.2 context
composer from Git, never the old application's runtime. Every completed response
is journalled; use a new output directory to retain evidence. Keyword checks are
partial diagnostics; apply the documented manual rubric before making quality claims.

The runtime protocol extension is backwards-readable. An already running observer
must be restarted to load new source; this resets its ephemeral AI conversation
and pairing token, but not the original EdgeLoop browser session or Ollama. Never
restart either Ollama service as part of an interface/backend source update.

## F2.4 character artwork

See [presentation architecture and development preview](F24_CHARACTER_PRESENTATION.md)
and the [inventory/missing states](F24_ARTWORK_INVENTORY.md). Edit only
`src/assets/characters/manifest.json` to configure exact model aliases, expression
references, placement and session-reaction policy. Reference approved local originals;
do not regenerate, rename or stage the archive as part of UI work. New public asset
references require checking rights and server allowlist behavior. No model rebuild
is involved. Development preview is opt-in at `/?characterPreview=1`.

Start/restart the fork static server and observer to load the new allowlist and ACK
metadata. Both use their existing launchers; never restart Ollama for an expression
change. Restarting the observer resets its pairing token. Reload the frontend only
after any active session is stopped normally. Tests, live-smoke limits and private
screenshot locations are recorded in the F2.4 validation document.
