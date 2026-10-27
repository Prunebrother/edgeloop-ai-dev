# F2.2 live character-model acceptance — 2026-10-27

All three requested character tags are compatible with the consolidated fork's
thinking-disabled streaming path. The existing 11435 server was already running,
so no daemon was started, stopped or restarted. Port 11434 was only inspected
with read-only requests; its PID remains unchanged.

The clean consolidated checkpoint `b3d7063` and thinking fix `7de7752` remain
intact. `backup/f22-pre-live-validation-20261027` preserves the latter before this
work. This follow-up adds test tooling/evidence/documentation only: production
observer, companion, UI, session logic and launchers are unchanged. Unrelated
untracked `Character_Art/` appeared during testing and was left untouched.

## Environment and compatibility

- Ollama 0.33.3, `OLLAMA_HOST=127.0.0.1:11435`,
  `OLLAMA_MODELS=/home/sean/.ollama/models`; `/api/tags` returns all 17 tags.
- Existing server configuration: one parallel request, maximum one loaded model.
- NVIDIA RTX 3080, 10240 MiB total. No unrelated process was terminated.
- Native `think:false`, `stream:true`, no tools. Each request preserves its selected
  embedded SYSTEM verbatim, checked against that exact tag's `/api/show` response.
- All final replies ended naturally (`stop`), with visible streaming deltas matching
  completed text and zero reasoning characters/chunks emitted. The final telemetry
  questions all reported 98 BPM, simulated data and RUNNING correctly.
- The three tags use the same existing base-weight blob
  `afb54ad43a39f947407f5cabc59856348d70e072baa5c62d436332157c151bcd`.
  No weights were copied, downloaded or rebuilt. No Modelfile or personality prompt changed.

## Performance

Final browser run, short sequential prompts, 8192 context, 256 output-token cap,
60-second keep-alive. Selection time is excluded. First-visible and completion
latency are measured from form submission; throughput is Ollama's generation rate.

| Model | First visible | First completion | Next completion | Warm tokens/s |
|---|---:|---:|---:|---:|
| `evelyn-lite-v1:latest` | 3.66 s | 4.89 s | 0.50 s | 99.6 |
| `evelyn-qwen35-stable:latest` | 0.67 s | 1.53 s | 0.55 s | 99.5 |
| `daisy-qwen35:latest` | 0.70 s | 1.11 s | 0.55 s | 99.6 |

Evelyn Lite's first request includes disk/GPU loading. The other tags reuse the
same base weights, so their first requests are not independent cold-load figures.
Warm first-visible latency was about 0.25 seconds. Short-output timings vary with
reply length; these are smoke measurements rather than a benchmark distribution.

The final run sampled 7826 MiB total GPU usage at peak (7.64 GiB) and 6650 MiB
for the 11435 runner (6.49 GiB). Ollama's `/api/ps` accounts for 5628493822 bytes
(5.24 GiB); the runner's larger allocation includes runtime overhead. Earlier
successful rounds reached 8274 MiB total while other desktop workloads differed.
No sample contained more than one resident model, and the server's cap was one.
The residency API retained the first tag's label across aliases; actual wire model
IDs and distinct embedded SYSTEM hashes confirmed the requested characters.

## Functional acceptance

An isolated copy of the current fork UI and actual observer implementation ran on
8780/8788 with temporary AI data. Real inference went only to 11435. Original
session controls used simulated 98 BPM and intercepted Handy HTTP; Bluetooth,
serial and microphone requests were denied. The normal 8770 dashboard and 8768
observer were not restarted or paired away from the user's browser.

Each character received two real prompts. Before the first prompt its history was
empty; the next inference contained only that model's marker/history. Switching
back to each tag restored its own visible conversation without either other marker.
Every switch left the original session RUNNING.

The test then closed only its own real inference socket after the first streamed
network chunk. A read error reached normal error handling; no incomplete turn was
stored, and the original session stayed RUNNING. Further test-client requests were
made unavailable using ConnectError. The original clock advanced from 10 to 13
seconds; pause/resume worked. Restoring the test transport recovered model listing,
selection and real inference. The original Stop then returned IDLE with zero output.
After resume, the harness waits for the authoritative RUNNING snapshot to propagate
before its recovery question; telemetry is projected at approximately one-second cadence.

## Remaining issues and limits

No transport/model-switching compatibility defect was found. Character prose can
still make unsupported interpretations: repeated rounds included an invented
"heart rate climb" at steady 98 BPM, descriptions of unobserved resting/posture,
and occasional omission of the requested simulation qualifier. This is a model
response-quality issue, independent of correct raw telemetry and isolated memory.
The final round's three basic telemetry fact checks passed, but that does not certify
factual consistency. No character behavior or prompts were changed to hide this.

A dropped stream leaves its partial bubble alongside a clear error, while excluding
it from memory. Thinking-enabled long generations and sustained concurrent load
were not re-benchmarked here. Existing thinking-budget regression coverage remains
passing. The existing Starlette/httpx TestClient deprecation warning remains.

## Tests, evidence and reproduction

98 Python tests passed, including four focused fixture guards: no forwarding to
11434/remote hosts, isolated interruption/recovery, exact identity auditing without
retaining prompts, and closure of only the test response stream. Ten bridge and
presentation tests passed. The original-source validator passed. Earlier 1057-test
upstream results remain historical baseline evidence; the engine was not changed
or rerun for this test-tooling-only follow-up.

Two initial harness problems were corrected before final acceptance: the static
asset allowlist needed the original Tailwind script, and completion must wait for
the speech frame rather than a transiently hidden cancel button. Neither required
an application change. GPU polling and completion timing were verified in repeated
real runs. Screenshots were visually reviewed at desktop and 390×844 mobile.

```bash
cd /home/sean/projects/edgeloop-ai-fork
# Existing 11435 must be running already, with MAX_LOADED_MODELS=1.
EDGELOOP_LIVE_ACCEPTANCE=1 \
  LIVE_ACCEPTANCE_REPORT=/tmp/edgeloop-live-unique-run \
  node tests/fork/live-acceptance.mjs
```

The opt-in script checks free fixture ports, starts only its own temporary UI and
observer, and closes only those child processes. It does not launch an Ollama
server. Linux/nvidia-smi and the existing local Playwright/Chromium installation
are required. Use a new output directory to preserve previous evidence.

See [summary](validation-f22-live.json), [full report](f22/live-acceptance/report.json),
[preservation checks](f22/live-acceptance/preservation.json), and
[screenshots](screenshots/f2.2-live/complete-desktop.png). Earlier successful rounds
are retained alongside the final report to document timing and quality variability.
