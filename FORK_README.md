# EdgeLoop AI experimental fork

This repository is a separate experiment based on original EdgeLoop **1.1.3**, commit **d351e011249079b368ebdc8d46f83b260be7d2a5**, under **AGPL-3.0-only**. The original [README](README.md), browser application, engine, rules, modes/goals, calibration, drivers, tests and license are unchanged. The 85-file [provenance manifest](docs/fork/upstream-pin.json) is checked by `tools/fork_validate.py`. `upstream` points to the original GitHub repository so later improvements can be merged on this experiment branch.

## Current milestone: F1 source/test baseline

The fork is ready for a manual localhost launch. Its original unit suites pass; UI/session acceptance is **pending** because this execution sandbox denies socket creation and Chromium startup. This is a clean source checkpoint, not a completed end-to-end AI demonstration. No AI bridge, panel, observer backend or command adapter has been installed. No custom B1/B2a coordinator is imported or run by this fork.

The existing project at `/home/sean/projects/edgeloop-ai/` is preserved at its B2a checkpoint `9e89fa1`, including its models, conversations and user files. The interrupted B2b implementation was not continued. See [AI reuse audit](docs/fork/AI_REUSE.md) and [architecture/pivot comparison](docs/fork/ARCHITECTURE.md).

## Start the original application on the host

From a normal host terminal:

```bash
cd /home/sean/projects/edgeloop-ai-fork
./tools/serve-local.sh
```

Open **http://127.0.0.1:8770/** in a fresh/private browser context with no stored device keys or hardware permissions. The launcher binds **127.0.0.1 only**, installs no service and starts neither Python AI nor Ollama. Stop the server with Ctrl+C. An alternate port can be supplied as the first argument.

The application retains the original age/setup screens, simulator, seven experiences, goals and controls. Use the original manual HR simulator for initial observation. Keep hardware disconnected; do not pair BLE, select serial devices or supply real device credentials. A full moving session normally requires toy readiness; the original automated smoke fixture supplies a **mock Handy API**, so manual HR simulation alone can correctly show WAITING FOR TOY. This is original readiness behavior, not a missing replacement engine. The fixture uses a fresh browser context rather than existing user profiles. Tailwind/PeerJS CDN resources may require network access on first load.

The fork works without Ollama and without the custom AI backend. **An observer-only AI service launch command will be added in F2.** The existing custom application's `edgeloop_ai.app:app` is not the fork's AI service: it constructs its own session coordinator. Running that entry point alongside the fork is not the planned integration.

## Validate

```bash
python3 tools/fork_validate.py
npm test
python3 tools/fork_validate.py --tests --report /tmp/edgeloop-fork-tests.json
```

The first command checks all original bytes; `npm test` is the unchanged upstream command. The per-file command reports actual subtest counts rather than Node 25's file-only summary.

Playwright was installed locally from the offline npm cache, without changing the original package manifest or lockfile. On a host where needed:

```bash
npm install --no-save --package-lock=false --ignore-scripts playwright@1.64.1
npx playwright install chromium
node tools/smoke.js . /tmp/edgeloop-fork-browser
```

`node_modules/` is already ignored upstream. The unmodified smoke tests mock Handy requests and exercise original UI/session controls. Run in an isolated environment with hardware disconnected. No real-device approval or safety verification is implied by a passing fixture. The sandbox attempt found Playwright and Chromium successfully, but Chromium then failed with `Operation not permitted`; see [validation](docs/fork/VALIDATION.md). No server was left running by this task.

## Next gates

1. **F1 host acceptance:** run the localhost application and browser smoke, record original simulator/lifecycle behavior without AI, and verify the fake-device boundary.
2. **F2:** reuse providers/model manager/Director/memory in an observer-only service, add authenticated read-only telemetry and optional streaming companion panel. Preserve the browser engine and model-specific memory.
3. **F3:** introduce simulated, manual/assisted high-level requests through original controller functions with explicit acknowledgements and replay/stop precedence tests. No calibration/reset/special-action/start tools.
4. **F4:** perform the full model/session/command/disconnect demonstration, then finalize the architecture decision. The current recommendation favors the original fork for engine fidelity, subject to this evidence.

No original project, historical data, Modelfiles or upstream source files were migrated, overwritten or deleted. No hardware or AI service was started.
