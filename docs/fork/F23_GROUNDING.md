# F2.3 — authoritative telemetry grounding

F2.3 keeps the original EdgeLoop engine authoritative and the companion read-only.
It projects validated, timestamped facts, separates settings from measurements and
places one fresh data block beside each question. Installed Modelfile SYSTEM text
is preserved verbatim; no character definitions, model weights, hardware drivers
or session calculations were changed.

See the [field-by-field audit](F23_TELEMETRY_AUDIT.md),
[canonical contract](SESSION_DATA_CONTRACT.md),
[example snapshot](f23/snapshot-example.json), [model-facing text](f23/snapshot-example.txt)
and [JSON schema](f23/session-facts.schema.json).

## Findings and changes

The prior bridge transported useful state, but the model context lacked resting,
single/dual settings and sample timestamps. It put raw JSON ahead of old dialogue,
accepted a boot/default pulse as potentially live, and exposed computed channel
percentages as a device velocity. None of those values proved physical movement.
Generated old replies could anchor subsequent current-session answers.

The observation adapter now reads actual sensor BPM independently of microphone
boost, current validated settings, original watchdog status and selected phase
fields. It does not call the mutating settings helper. Capture/measurement/receipt
times remain distinct. Unknown readings and uncomputed pullback are null.
Connection, readiness, session status and physical movement remain distinct.

The observer independently validates and timestamps the projection. Currentness
expires after five seconds; BLE needs a verified recent sample. Trend evidence is
bounded to 12 unique samples over 15 seconds, requires four samples spanning three
seconds, and cannot cross a gap/source/new-session boundary. Recent events require
an actual observed state change and are bounded, ordered and deduplicated.

The model receives one compact runtime block, never accumulated telemetry turns.
Current-session questions omit historical telemetry dialogue from that inference;
model-specific stored conversations and personal dialogue remain intact. The exact
native SYSTEM is retained, followed only by factual/read-only boundaries. A narrow
explicit-claim checker allows one correction; a still-conflicting draft is removed
and not saved. Snapshot currentness is checked both before inference and before
accepting a completion, including slow-generation expiry.

## Reproducible validation

Commands are in [development](DEVELOPMENT.md). The 20 synthetic scenarios cover idle,
simulator, mocked BLE, settings versus measurements, connection loss, paused/stopped
state, valid rising/fluctuating samples, stale data, experience/goal/edge/intensity
changes, missing values, restart, malformed input and a current question after 64
old dialogue turns. No physical session or driver API is used.

The opt-in evaluator compares pinned F2.2 context (`370fe0b`) with grounded context
using the same snapshots, question, history, temperature 0, 8,192 context, 512 output
tokens and exact native instructions. The three requested models run sequentially
on the existing 11435 server, thinking disabled, with one resident base model.
This compares context construction on shared validated inputs, not a replay of the
entire old observer. Baseline always runs first; cache/order effects are not
controlled, so latency is descriptive rather than a randomized performance study.
Temperature zero is not a guarantee of reproducibility across runtime versions.
Results include all replies/errors, first-token and completion latency, prompt
counts, correction attempts, SYSTEM hashes, source hashes and GPU samples. Models
sharing a base blob can appear under the first resident tag in `/api/ps`.

Keyword checks are partial regression indicators, **not a factual-accuracy score**.
They can miss wordings and causal speculation, or flag legitimate references to a
setting or a stable connection. All errors and blocked generations count separately;
missing output is never scored as a successful factual response. Live results are
one local sample, not proof that a model will never hallucinate. Native instructions
were neither edited nor replaced to improve the benchmark.

### Manual review rubric

Read the question, canonical facts and full paired responses. For each reply mark:

1. Numerical claims: exact current value/units; settings and old values named as such.
2. State and devices: engine status/connection accurate; physical activity unknown.
3. Uncertainty: missing/stale data unavailable, with no numeric guess or diagnosis.
4. Events/trends: only timestamped evidence supports temporal claims; no invented causes.
5. Character continuity: recognizable native vocabulary/style without prescribed app tone.

Use pass, partial, fail or not applicable, with quoted evidence. This checkpoint's
spot review is by the implementing agent, not blinded or an independent user study.
Technical preservation of SYSTEM is checked independently of subjective style.

## Remaining limits

- The authenticated browser is the authority, not a signed sensor or independent
  hardware verifier. No physical feedback is collected; disconnection does not
  prove that a motor stopped.
- The explicit-claim checker is a conservative collection of patterns. It misses
  some indirect, causal, emotional and qualitative assertions and may reject a
  legitimate unusual phrasing. It is not an emotion classifier or a safety layer.
- Models still add speculative language about calmness, anticipation, nervous systems,
  sensor faults or the cause of a gap, despite boundaries. Those interpretations
  are not established by BPM. Personality preservation does not certify factuality.
- Streamed tokens are provisional. A false draft can appear briefly before reset;
  a second conflict produces an explicit error rather than fabricated fallback text.
- Runtime facts are larger than the prior ambiguous raw summary. Measured token and
  latency overhead are reported with the live results; a correction adds a generation.
- Current-session inference omits historical telemetry dialogue to avoid anchoring.
  Stored history is retained, but mixed personal/session messages may also be omitted
  for that inference. Explicit historical questions retain the dialogue.
- Freshness assumes browser/backend share the local host clock. Large clock changes
  conservatively invalidate readings. Phase values are original counters/projections,
  not a second timer or a new session controller.
- Live comparative evaluation uses thinking disabled. Thinking parsing/budget behavior
  is regression-tested with synthetic streams; this milestone is not a full live
  thinking-mode quality benchmark.
- Existing Starlette/httpx TestClient deprecation warning remains.

F2.2 and live-validation commits and the pre-F2.3 backup ref remain intact. Both
Ollama servers/stores and the legacy project remain intact. Concurrent character
artwork edits are deliberately excluded from this checkpoint.

## Live comparison results

Final frozen-source run: 20 scenarios × three models × baseline/grounded = 120 replies.
All source hashes, including fixtures and evaluator, are stored in the raw report.

| Model | Keyword checks, baseline → grounded | Median completion seconds, baseline → grounded | Mean total prompt tokens, baseline → grounded | Grounded corrections / errors |
|---|---|---|---|---|
| `evelyn-lite-v1:latest` | 35/43 → 37/43 | 1.315 → 1.347 | 1028.7 → 1226.1 | 0 / 0 |
| `evelyn-qwen35-stable:latest` | 34/43 → 40/43 | 2.152 → 2.813 | 2176.9 → 2443.1 | 0 / 0 |
| `daisy-qwen35:latest` | 32/43 → 38/43 | 1.427 → 1.478 | 2257.9 → 2524.1 | 0 / 0 |

Peak GPU usage: **8701 MiB** whole GPU of 10,240 MiB; **6650 MiB** Ollama runner; maximum **1** resident base model. Whole-GPU usage includes the desktop/browser. No unrelated process was terminated.

The three model tags preserved exact native SYSTEM hashes. All accepted responses used visible streaming with thinking disabled. The 17-model discovery inventory is recorded. Mean prompt tokens include correction calls; completion time is end-to-end. Final-attempt first-token timing is separate in the [summary](f23/evaluation-summary.json). Native instructions differ substantially in size, so cross-character token totals are not comparable personality-efficiency rankings.

Read the [full results with source hashes and GPU samples](f23/model-evaluation.json), [raw paired responses](f23/responses.jsonl) and [partial check breakdown](f23/evaluation-summary.json). A correction/error is not hidden as a successful generation. Keyword matches do not establish correct roles, causality, emotional interpretation or character quality.

### Interpretation of these results

The numerical-presence check was already 57/57 in baseline and remains 57/57;
it does not prove correct attribution of a number. Unknown-HR wording improves
from 1/9 to 8/9 and unknown-connection wording from 0/3 to 3/3. The trend-uncertainty
keyword check declines from 6/12 to 3/12; some natural wording is missed, but real
unsupported trend/causal claims also remain. No correction was triggered by the
narrow checker in this frozen live run; synthetic regressions separately verify
its correction and rejection paths.

Read the [manual spot review and concrete failures](f23/manual-review.md). Notably,
Lite invents a climb from the resting setting, Stable infers a possible connection
from sensation and Daisy invents a two-minute warm-up in one reply. These are
accepted-output limitations, not transport failures. **The broad model-quality
success criterion is not fully met.** The checkpoint establishes better data,
provenance, bounds and reproducible evidence, while preserving all original safety
boundaries. It must not be advertised as preventing hallucinations or validating
physiological interpretations.

## Software and browser acceptance

- Original upstream: **1,057/1,057**, 32 files. All 81 pinned source files remain unchanged; four existing integration files retain reviewed hashes.
- Consolidated Python: **183/183**. Bridge/presentation: **13/13**. Existing dashboard harness passed.
- Mocked-device Playwright passed responsive desktop/tablet/mobile, prompt freshness/settings, thinking retry, factual rejection, scrolling, cancellation and offline original controls.
- Final real-model Playwright passed streaming, thinking off, all three model histories/restoration and isolated midstream/connection failure with original timer, pause/resume and stop intact. Neither Ollama daemon was interrupted.
- Desktop/mobile screenshots were visually reviewed. [Mocked browser evidence](f23/browser/report.json), [real browser evidence](f23/live-browser/browser-report.json), [complete validation record](validation-f23.json).

The ordinary observer was restarted once to load the new code; its pairing token
and in-memory conversation reset. The dashboard remains at `http://127.0.0.1:8770`
and observer at `ws://127.0.0.1:8768/observe`. New credentials are in the private
local startup log `/tmp/edgeloop-f23-observer-ready.log`, never in Git or screenshots.
An initial startup attempt hit the old socket's TIME_WAIT state; no other process
was stopped, and startup succeeded after that state cleared. Both Ollama PIDs and
both model stores remain unchanged. Original browser/session controls were not
restarted. If the browser has an active session, stop it normally before reloading
the updated frontend. Only simulated/mocked sessions were used for validation.
