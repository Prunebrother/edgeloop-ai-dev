# F2.1 validation — 2026-10-27

The three-column interface passes the original 1057 tests, 16 observer tests, eight JavaScript bridge/presentation tests 221 preserved AI regression tests, the original AI dashboard harness 221 preserved AI regression tests, the original AI dashboard harness and the expanded Playwright suite. Desktop/tablet/mobile screenshots were visually inspected. See [F2.1 implementation and commands](F2_1_INTERFACE.md) and [browser evidence](screenshots/f2.1/report.json). The previous browser sandbox block was resolved by elevated execution for Chromium and temporary loopback fixtures. Live Ollama quality and physical hardware remain unverified; F3 has not begun.

The records below describe earlier checkpoints and their limitations at that time.

---

# F2 validation — read-only implementation checkpoint

F1 backup tag: `backup/f1-e651754`. F2 is implemented and automated protocol/adapter validation passes. **Host browser and live Ollama acceptance remain outstanding; F3 has not begun.** See [implementation/security/launch](F2_READ_ONLY.md).

| Check | Result | Scope |
|---|---|---|
| Observer/API protocol | **15 passed** | Real FastAPI WebSocket/TestClient with existing AI classes; auth/origin/host, redaction, model-context preservation, command/native-tool rejection, queues/sequence/epoch/retired session, stale/expired/oversized/binary input, slow-model telemetry continuity, safe disconnect and static private-data isolation |
| JavaScript capture/connection | **7 passed** | Original-state projection, hidden target/key/history redaction, measured trend, IDs/event coalescing, disabled/unavailable/reconnect behavior, urgent stop, backpressure and ignored command objects |
| Original upstream tests | **1057 passed / 32 files** | Unchanged original test files; all original engine/rules/patterns/drivers are untouched. Three reviewed optional-extension changes are separately hashed |
| Preserved AI backend | **221 passed** | Isolated test data; existing model/memory/Director/tool/safety regressions; original checkout unchanged |
| Preserved dashboard DOM harness | **Passed** | Existing dashboard tests; this does not substitute for browser acceptance of the new panel |
| Source/syntax | **Passed** | 82 unchanged pinned files plus exact reviewed hashes for `app.js`, `sw.js`, `.gitignore`; Node syntax, Python compilation, shell syntax, diff checks |
| F2 Playwright original UI + fake Handy + mocked AI | **Blocked** | `node tests/fork/browser.mjs` fails before UI steps: Chromium `sandbox_host_linux.cc` / `shutdown: Operation not permitted`. Fixture code is supplied for host execution, not claimed passed |
| Live Evelyn/Daisy/Mira questions | **Not verified** | The model-switch tests use mocked local Ollama transport for these model identifiers. Actual generation/quality requires running Ollama/models on the host |
| Hardware | **Disconnected** | No real Handy/BLE/serial connection or physical-safety verification; the host fixture intercepts Handy and rejects native device permissions |

The observer tests run through `/tmp/run_fork_tests.py`, the established restricted-runner selector adjustment (10 ms polling for blocked TestClient socketpair wakeups); no assertions are skipped. A normal host runs ordinary pytest. One existing Starlette/httpx deprecation warning remains. Playwright is installed; missing browser software is not the current block. A jsdom offline-cache attempt lacked dependencies and was not used as browser evidence.

Commands used:

```bash
PYTHONPATH="$PWD:/home/sean/projects/edgeloop-ai" /home/sean/projects/edgeloop-ai/.venv/bin/python /tmp/run_fork_tests.py -q tests/fork
node --test --test-isolation=none tests/fork/bridge.test.mjs
python3 tools/fork_validate.py --tests --report /tmp/edgeloop-f2-upstream.json
node tests/fork/browser.mjs
# In the existing AI checkout, with isolated data:
EDGELOOP_DATA_DIR=/tmp/edgeloop-f2-old-regression .venv/bin/python /tmp/run_edgeloop_tests.py -q
node tests/dashboard_ui.cjs
```

No runtime service is claimed running in this sandbox. Both launch scripts require normal host socket permissions. No old B1/B2a controller is started by the observer factory, and no controller is substituted if AI disconnects. Last-observed values are retained diagnostically while unavailable context is withheld from inference. Original Stop remains entirely in original JavaScript; backend stop *observations* only cancel AI output and do not operate devices.

The existing AI Director's flat-schema context filter required a narrow subclass to retain the nested validated original-state projection. Its policy/memory/repetition logic and all provider/model code are reused. Event-generated model responses are disabled in F2; the Director receives bounded semantic events for subsequent user dialogue. Native tools and control routes are absent. No identities/personality prompts are added; the shared provider preserves original Modelfile system identity alongside neutral runtime context.

Before F3: complete original/fork host browser smoke with backend available and unavailable; run real selected-model session questions and confirm model switching during the same original session, updated HR/event context, quiet unsolicited behavior, original Stop with the AI service down, and private-data/source-cache isolation. F3 then requires its own explicit consent, simulation-only execution boundary, original guarded routing and command-ack/replay/priority validation. No bidirectional controls are implemented in F2.

---

# Archived F1 source/test baseline validation

Date: 2026-10-27. Fork branch: `experiment/ai-companion`. Pinned original: EdgeLoop **1.1.3**, **d351e011249079b368ebdc8d46f83b260be7d2a5**. The existing AI project is preserved at B2a `9e89fa1`; its pre-existing uncommitted files remain untouched. No interrupted B2b implementation was added.

## Results

| Check | Result | Evidence / limitation |
|---|---|---|
| Original source integrity | Pass | All 85 original files match the recorded SHA-256 values, including original app/engine/patterns/rules/state/drivers, index, package manifest, README, `.gitignore` and license |
| Git provenance / update path | Pass | Separate repository cloned with original history; experiment branch descends from pin; `upstream` is `https://github.com/marshallmims/edgeloop` |
| Unchanged upstream `npm test` | Pass | 32/32 test files, zero failure/skip/cancellation, approximately 165 s |
| Per-file original unit runs | Pass | 1057/1057 tests in 32 files, zero failure/skip/cancellation; [machine report](upstream-tests-f1.json) |
| Existing AI backend regression | Pass | 221 tests, zero failures; existing selector-polling wrapper for restricted TestClient wakeups; isolated `/tmp/edgeloop-fork-baseline-ai-tests` data directory; existing Starlette/httpx deprecation warning |
| Existing dashboard DOM harness | Pass | Metrics, streaming/cancellation, silence, memory isolation, text safety, emergency, activation/provenance and disconnect checks; not a browser test of this fork |
| Local test dependency environment | Prepared | Playwright 1.64.1 installed from offline cache into ignored local `node_modules`; original manifest/lockfile unchanged; cached Chromium available |
| Original localhost server | Blocked | `python3 -m http.server 8770 --bind 127.0.0.1` fails at socket creation with `PermissionError: [Errno 1] Operation not permitted` |
| Original browser smoke | Blocked | Unmodified `node tools/smoke.js . /tmp/edgeloop-fork-f1-browser` finds Playwright/Chromium but Chromium fails `sandbox_host_linux.cc`, `shutdown: Operation not permitted`; exit 2 |
| Original UI, live simulator/session lifecycle | Pending host acceptance | No visual/session browser pass is claimed. Source identity and pure/module tests do not substitute for runtime UI verification |
| Live model / AI bridge / optional panel | Not implemented/tested | F2–F4 remain pending; no read-only or bidirectional bridge is claimed |
| Hardware | Disconnected | No real device was connected or commanded; original fake-API unit suites run independently of real drivers |

The current restriction is **not missing Playwright**: local installation succeeded. This execution sandbox rejects localhost socket creation and Chromium IPC. No running localhost application is claimed. No server, Ollama process or AI service was left running by this task. The original smoke's spawned HTTP child also cannot create its socket here.

Source fidelity preserves the complete original implementation of modes, goals, calibration, intensity, hardware and guards. Runtime equivalence in a local browser remains unverified until host acceptance. The existing custom coordinator is not imported into this fork, and no production AI service was started in parallel. Backend regressions run only their existing isolated test fixtures.

## Commands executed

In the fork:

```bash
npm install --offline --no-save --package-lock=false --ignore-scripts --no-audit --no-fund playwright@1.64.1
npm test
python3 tools/fork_validate.py --tests --report /tmp/edgeloop-fork-f1-tests.json
python3 tools/fork_validate.py
python3 -m http.server 8770 --bind 127.0.0.1
node tools/smoke.js . /tmp/edgeloop-fork-f1-browser
```

In the preserved AI project:

```bash
EDGELOOP_DATA_DIR=/tmp/edgeloop-fork-baseline-ai-tests .venv/bin/python /tmp/run_edgeloop_tests.py -q
node tests/dashboard_ui.cjs
```

`/tmp/run_edgeloop_tests.py` is the existing restricted-runner adjustment: it caps `selectors.EpollSelector.select` waits at 10 ms so threaded Starlette TestClient can wake without socketpair writes, then invokes ordinary pytest. No assertions were disabled. On an unrestricted host use `EDGELOOP_DATA_DIR=/tmp/edgeloop-ai-test-data .venv/bin/python -m pytest -q` instead.

## Host gate before F2

1. Launch `./tools/serve-local.sh` from a normal terminal and visit `http://127.0.0.1:8770/` in a fresh/private browser context without device credentials or hardware permissions.
2. Run the original Playwright smoke with isolated browser storage and mocked Handy transport; inspect its report/screenshots and errors. Keep real devices disconnected; do not grant hardware permissions. Verify original age/setup UI, simulator HR sweep, original guarded Start/Pause/Resume/Stop/Reset and simulated session history.
3. Confirm all seven experiences/goals/calibration remain available, the session continues with no AI backend/Ollama, and no real hardware API escapes the mock. A manual HR slider alone does not satisfy original toy readiness.
4. Record this result as F1 runtime acceptance. Only then add optional observation/chat integration. F2 must prove that importing/starting its service cannot create the B1/B2a coordinator; F3 must prove authorization, actual guarded application, replay/stop precedence and no physical control.

This source checkpoint is deliberately clean while the environmental host gate is outstanding. The requested F2 telemetry/chat, F3 commands and F4 live demonstration are not implemented. The [comparison](ARCHITECTURE.md#comparison) is a provisional engineering recommendation, not evidence that the full experiment has passed.
