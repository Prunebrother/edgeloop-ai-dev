# EdgeLoop AI experimental fork

This repository is a separate experiment based on original EdgeLoop **1.1.3**, commit **d351e011249079b368ebdc8d46f83b260be7d2a5**, under **AGPL-3.0-only**. The original engine, rules, patterns, modes/goals, calibration, drivers, tests and license are unchanged. Three reviewed changes add the fail-isolated observation hook, AI cache exclusion and private-data ignores. The immutable 85-file [base manifest](docs/fork/upstream-pin.json) plus [reviewed changes](docs/fork/f2-changes.json) are checked by `tools/fork_validate.py`. `upstream` points to the original GitHub repository so later improvements can be merged on this experiment branch.

## Current milestone: F2 read-only implementation checkpoint

The fork now has an optional authenticated AI companion that observes original browser state, reuses the existing Ollama/model/Director/memory classes, and streams user chat. **No AI command or hardware-control path exists.** The original project is preserved; the observer imports no custom session controller. F1 is backed up locally by tag `backup/f1-e651754`.

See [F2 launch, architecture, security and acceptance](docs/fork/F2_READ_ONLY.md). Automated protocol/adapter regressions pass. Full browser and live-model acceptance remain blocked/unverified in this environment; **F3 has not begun**.

## Start the original application on the host

From a normal host terminal:

```bash
cd /home/sean/projects/edgeloop-ai-fork
./tools/serve-local.sh
```

Open **http://127.0.0.1:8770/** in a fresh/private browser context with no stored device keys or hardware permissions. The launcher binds **127.0.0.1 only**, installs no service and starts neither Python AI nor Ollama. Stop the server with Ctrl+C. An alternate port can be supplied as the first argument.

The application retains the original age/setup screens, simulator, seven experiences, goals and controls. Use the original manual HR simulator for initial observation. Keep hardware disconnected; do not pair BLE, select serial devices or supply real device credentials. A full moving session normally requires toy readiness; the original automated smoke fixture supplies a **mock Handy API**, so manual HR simulation alone can correctly show WAITING FOR TOY. This is original readiness behavior, not a missing replacement engine. The fixture uses a fresh browser context rather than existing user profiles. Tailwind/PeerJS CDN resources may require network access on first load.

The fork works without Ollama and without the custom AI backend. **For optional AI, start `./tools/serve-ai.sh` in a second terminal and pair using the token printed there.** The existing custom application's `edgeloop_ai.app:app` is not the fork's AI service: it constructs its own session coordinator. Running that entry point alongside the fork is not the planned integration.

## Validate

```bash
python3 tools/fork_validate.py
npm test
python3 tools/fork_validate.py --tests --report /tmp/edgeloop-fork-tests.json
```

The first command checks 82 untouched original files and the exact hashes of three reviewed optional-extension changes; `npm test` is the unchanged upstream command. The per-file command reports actual subtest counts rather than Node 25's file-only summary.

Playwright was installed locally from the offline npm cache, without changing the original package manifest or lockfile. On a host where needed:

```bash
npm install --no-save --package-lock=false --ignore-scripts playwright@1.64.1
npx playwright install chromium
node tools/smoke.js . /tmp/edgeloop-fork-browser
```

`node_modules/` is already ignored upstream. The unmodified smoke tests mock Handy requests and exercise original UI/session controls. Run in an isolated environment with hardware disconnected. No real-device approval or safety verification is implied by a passing fixture. The sandbox attempt found Playwright and Chromium successfully, but Chromium then failed with `Operation not permitted`; see [validation](docs/fork/VALIDATION.md). No server was left running by this task.

## Roadmap and remaining gates

- F1 source/test checkpoint: `e651754`; local backup tag `backup/f1-e651754`. Host original-UI acceptance is still pending.
- F2 implemented: read-only observation, shared AI service and optional streaming panel. See [validation](docs/fork/VALIDATION.md). Run browser and live-model acceptance on the host before F3.
- F3 not started: simulated, explicitly authorized high-level requests through original controls, acknowledgement states and safety/replay tests.
- F4 pending: full demonstration, disconnect/reconnect acceptance and final architecture decision. The original-fork architecture remains the provisional recommendation.

The static launcher excludes private AI data and server code. Both services bind loopback and are manually started. No original project, historical data, Modelfiles or core upstream calculations were migrated or overwritten. No physical device was connected and no AI control/voice/artwork feature was added.
