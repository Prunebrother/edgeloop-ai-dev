# F2.5 implementation and acceptance — 28 October 2026

F2.5 adds model-selected expressions, centrally enforced thinking OFF, and verified
significant-event opportunities in the existing read-only companion. The engine,
hardware drivers, authentication, original safety actions and device permissions
are unchanged. Transport/browser acceptance passes; **semantic model quality is
still imperfect**. Expression-format success must not be read as factual accuracy.

## Recovery and scope

Starting branch: `experiment/ai-companion`, HEAD `553af45` (corrected F2.4 catalog),
preceded by `6ae67aa` (presentation) and F2.3 `2aae519`. No tracked edits existed.
The original untracked `characters/models/daisy-lite/` remains untracked and
unchanged. Its tar backup is `.git/f25-backups/edgeloop-f25-untracked-daisy-lite-20261028.tar`;
the tracked starting state is `backup/f25-before-20261028`. No artwork was edited,
renamed or generated; no Ollama model was rebuilt, moved or overwritten.

Checkpoints: A `5a8f7d7` (transport/parser), B `b3addce` (presentation), C `10ac480`
(events/configuration), D `35924cd` (live hardening/evidence), followed by the
F2.5-E final documentation/checkpoint commit. Earlier intermediate commits are
recoverable development stages; use the final checkpoint for the complete suite.

## One expression protocol

Version 1: `[[expression:proud]]` followed by ordinary dialogue. The literal word
`expression` is required. A header changes delivery, never telemetry or hardware.
The allowed IDs, matching both existing artwork catalogs, are exactly:

`neutral`, `happy`, `playful`, `flirty`, `mischievous`, `focused`, `excited`,
`surprised`, `disappointed`, `concerned`, `proud`, `comforting`.

A header permits a portrait update before dialogue without buffering the reply,
a JSON envelope, a classification call, or a replacement transport. The runtime
instruction describes formatting only. The Ollama transport retrieves the native
Modelfile SYSTEM and prepends it verbatim to the application runtime SYSTEM,
exactly once. Live audited requests verify this composition; models retain their
native scientist/farm-owner identities. No alternative persona system was added.

`ExpressionStream` handles arbitrary content-frame fragmentation, with at most
64 envelope characters, a short delimiter prefix and a reasoning-close suffix.
Only the first leading canonical header can select an expression. Duplicate,
invalid and incomplete reserved metadata cannot select another expression.
Double-bracket envelopes containing a colon are reserved presentation data;
malformed model variants such as `[[happy:98]]` and `[[tone:playful]]` are discarded,
**not accepted as additional protocols**. Ordinary `[[prose]]`, long ordinary
bracket prose and single brackets remain text. Overlong reserved envelopes are
discarded through their terminator/newline. Truncated reserved prefixes are dropped.

The shared collector removes metadata before streaming, factual checks, repetition
assessment, speech preparation and memory. Dedicated API `message.thinking` fields
never enter the collector; legacy inline `<think>` blocks are also suppressed.
No raw reasoning is logged. Whitespace/prose streams incrementally after the
bounded prefix resolves. Existing unsolicited-response suppression still buffers
an event's dialogue until factual/repetition checks accept it; ordinary user chat
streams incrementally. This intentionally preserves F2.3/Director protections.

## Thinking OFF and compatibility

`config/ai.toml` is the backend runtime configuration:

```toml
[inference]
thinking = false
explicit_expressions = true
```

F2.5 rejects `thinking = true`; no development ON override is implemented. The
transport always sends Boolean `think: false` on `/api/chat`, including event,
revision and factual-correction requests. `/api/generate` is used only to unload
and also sends `think: false`. Saved legacy ON settings and per-model presets
cannot enable thinking during startup, switching, discovery, restoration or
reconnection. The old standard UI toggle is hidden and has no enable action.

Modern `/api/show` thinking values excluding Boolean false cause an explicit
compatibility rejection. The tested Ollama 0.33.3 server omits that metadata for
its Qwen3/Qwen3.5 models: the documented older-capability path sends false
explicitly and validates the actual server response. HTTP 400/422 is an explicit
protocol compatibility error. There is no parameter-removal retry, enable-thinking
retry or Modelfile modification. An unexpected separate reasoning channel is
suppressed and recorded as `unexpected_reasoning_suppressed`; it is not proof of
compliance. Select another compatible model if this persists.

References: [Ollama chat API](https://docs.ollama.com/api/chat) and
[thinking controls](https://docs.ollama.com/capabilities/thinking). Absence of
visible reasoning alone does not establish that thinking was disabled; the tests
inspect outbound Boolean payloads as well.

## Authoritative event audit and policy

Sources remain `Capture.project` → strict `Observation` →
`BrowserObservation.event_evidence`. Every accepted event requires two consistent,
fresh source projections; a kind/ID alone is insufficient. Event IDs, session ID,
sequence, source `at_ms`, receipt age and transition evidence remain separate from
model output. Browser timestamps use captured wall-clock milliseconds. F2 legacy
frames may omit event timestamp/session ID; then the accepted snapshot/session and
receipt time scope the derived transition, without inventing a source timestamp.

| Actual event | Required transition/source fields | Meaning and priority |
| --- | --- | --- |
| `session_started` | IDLE → RUNNING status; session identity | Observed engine start; major |
| `session_resumed` | PAUSED → RUNNING/RAMPDOWN, same session | Observed resume; major |
| `pause` | RUNNING/RAMPDOWN → PAUSED | Pause notice immediately; routine for AI scheduling |
| `stop` | non-IDLE → IDLE | Immediate stop notice; major commentary candidate |
| `edge` | same-session `edges` counter increases | Engine-counted edge, not inferred from BPM; major |
| `milestone` | `seconds // 300` increases, same session | Derived five-minute elapsed boundary, **not goal completion**; major |
| `signal_lost` / `no_contact` | signal becomes stale / contact flag becomes true | Observed source fault; critical immediate notice |
| `device_changed` | device projection changes | Critical if a reported BLE/Handy/Intiface/TCode/VacuGlide connection is lost during a non-IDLE session; otherwise routine |
| `signal_restored` | stale → OK signal | Routine; reconnect alone does not manufacture an event |
| `experience_changed`, `goal_changed`, `intensity_changed` | corresponding selected value changes | Routine settings; not achieved goals or physical output |
| `threshold_changed` | maximum-setting fields change | Routine configuration, **not a threshold crossing** |
| `mode_changed` | changed experience/goal | Legacy accepted alias; routine; current Capture emits specific kinds |

Goal completion, threshold release, Came Early, Force Orgasm, emergency-stop cause
and named safety intervention are not separately exported/proven event kinds in
this contract. They were not invented. Their existing engine/UI behavior remains.
Stop/pause/status may be observed without claiming the particular underlying cause.
Simulated HR remains labeled simulator data; physical movement feedback is unknown.

All events can be repeated or stale. Existing F2.3 checks reject future/old event
timestamps (five-second capture window), wrong sessions, invalid sequence and
unproven transitions. History is bounded (32 source events, six current-context
events, 256 dedup IDs); old sessions are retired. Reconnect requires new transition
evidence, not replay. Session resets clear pending/recent dialogue events; switching
models clears undispatched opportunities. Routine events update context silently.

The existing Director decides when: 45-second speech spacing, 60-second per-kind
cooldown and event TTL, 15-second user grace, plus Director topic/category pacing
(default 120-second spontaneous spacing and 30-second user idle). Queue limit is
eight. Active generations are not interrupted by queued milestones. Critical
notices cancel AI output immediately and never await inference. Their notices do
not operate hardware. Engine safety is independent. A model chooses its own
expression; there is no event-to-emotion table in the production path.

## Presentation, memory and diagnostics

Existing renderer/controller are reused. Metadata frames carry protocol version,
response ID, generation and explicit provider/model identity; the existing shared
manifest resolves that model to a character. Different Evelyn variants share art
but retain provider/endpoint/model-scoped histories. Daisy Lite's discovered exact
alias was added. Unknown models remain generic. Activity is independent of emotion;
a new user turn or Stop no longer imposes Focused/Neutral. Last expressions persist.
Accepted expression IDs are stored as a separate assistant field, never marker text,
and restored from the existing memory store. Old assistant content is sanitized on
restoration. Cancellation stores no partial reply. Request/model/generation guards,
connection epochs and bounded cancelled IDs reject late updates, including after
switches/reconnections. New characters reset presentation to Neutral.

All 24 original portraits currently exist; none is missing. Missing/failed future
variants retry Neutral, then a placeholder. The renderer still loads only the
requested image, reuses an unchanged source, keeps at most two transition layers,
uses original aspect ratios and respects reduced motion. No full-library preload
or second image cache was added. Desktop columns and mobile Session/Chat/Character
views remain; Emergency stop and the chat composer remain accessible.

On localhost only, `?characterPreview=1` exposes the existing artwork preview and
collapsed runtime diagnostics: endpoint/model/identity, thinking status, expression
and source, activity, last proven event/priority, Director decision, validity,
portrait/fallback and inference status/error. No pairing token or reasoning is
included. Set `explicit_expressions = false` and restart the companion service to
restore conservative dialogue classification; markers are still sanitized and
thinking remains OFF. Existing portrait/activity selection creates no model call.

## Acceptance results and evidence

[Evidence directory](f25/) includes logs, synthetic fixtures, live measurements and
screenshots; no pairing credentials, personal histories or native SYSTEM text.

| Check | Result |
| --- | --- |
| Original upstream suite | 1,057 passed; original engine/safety files match reviewed pin |
| Consolidated Python | 225 passed; one existing FastAPI/Starlette deprecation warning |
| Bridge/presentation | 24 passed |
| Dashboard Playwright | Passed; mock Ollama/Handy, no physical devices |
| Character Playwright | Passed; 24 portraits, streaming metadata, verified milestone, fallback, diagnostics, cancellation, 1920×1080 / 2560×1440 / 1366×768 / 390px |
| Live browser | Passed for Evelyn Lite, Evelyn Stable and Daisy; native SYSTEM preservation, actual streaming, isolated/restored memory, midstream failure/recovery, engine timer/pause/resume/stop independence |
| Live scenario matrix | 38 completed turns across those three plus `qwen3:8b`; 36/38 valid expressions (94.7%); two deterministic fallbacks; zero visible metadata or reasoning-channel output |

The final matrix audited 44 chat calls: 38 scenarios, three bounded existing factual
corrections and three no-envelope comparison turns. All sent false; no separate
expression inference occurred. Scenarios include greetings, jokes, serious/supportive
conversation, surprises, idle/running/paused simulation, disconnected hardware,
stale telemetry, counted-edge questions and the same verified event opportunity.
Observer reconnection, cancellation, session reset and routine-event silence also
have automated coverage; browser switching/cancellation/outage coverage is separate.

| Model | Valid headers | Median first visible / total seconds | Median generation tokens/s |
| --- | --- | --- | --- |
| Evelyn Lite Qwen3.5 | 12/12 | 0.280 / 1.226 | 101.1 |
| Evelyn Stable Qwen3.5 | 11/12 | 0.307 / 1.379 | 98.8 |
| Daisy Qwen3.5 | 11/12 | 0.690 / 1.320 | 96.6 |
| Qwen3 8B | 2/2 | 1.472 / 1.820 | 104.9 |

These are small, warmed samples, not service-level guarantees. Browser cold/switch
turns were slower (about 3.4–5.8 seconds end-to-end). Live browser monitoring saw
at most one resident model, peak runner memory 6,650 MiB and total GPU use 7,991 /
10,240 MiB. Matrix `/api/ps` reported approximately 5,368 MiB for Qwen3.5 models and
5,900 MiB for Qwen3; measurement methods/context differ. Residency/unload policy
was not changed. The instruction adds 524 characters / approximately 110 measured
prompt tokens versus matched no-envelope turns. Header generation adds a few tokens.
No-envelope greeting baselines took 0.989 / 1.538 / 1.187 seconds respectively;
ordering, caching and different generated wording prevent a causal speed claim.

## Remaining limitations and troubleshooting

Format reliability improved after real models emitted malformed `[[happy:98]]`
and `[[tone:playful]]` headers; those drafts motivated generic bounded suppression.
Missing headers remain valid legacy behavior. The final 94.7% rate is not perfect
reliability and says nothing by itself about emotional appropriateness. All three
chose Comforting for supportive turns; Playful dominated many other scenarios.
Evelyn Stable sometimes chose Focused/Mischievous; model-specific voice remained
recognizable. Repetition and excessive session narration remain model-quality issues.

Factual checks are conservative heuristics, not semantic verification. Live review
still found unsupported bodily/health speculation, rhetorical posture assumptions,
physical-motion assumptions from disconnection, and character responses that did
not actually acknowledge the triggering edge. Daisy did not explicitly state the
running status in one browser answer. The F2.5 guard adds regression-covered checks
for explicit unmeasured pulse, posture and safety assertions, with the existing
single correction/error path; it cannot detect every paraphrase or rhetorical
question. Passing live gates establishes transport, provenance, known checks and
isolation, **not perfect factual or conversational quality**. Character dialogue
and portraits must never be used as authoritative state. Original controls and
canonical telemetry remain the source of truth.

For wrong expressions, inspect validity/source first; verify the exact header and
manifest asset status. Missing headers use the conservative mapper or retain the
previous expression. Do not add keyword-to-event emotion rules. For reasoning,
verify actual payload false and model `/api/show`; inspect compatibility status,
then select another compatible model. Never remove false, enable thinking on retry,
edit a Modelfile or treat a hidden panel as a fix. For stale telemetry, re-pair and
wait for a fresh projection; neither old memory nor model prose repairs evidence.

Future TTS must consume only sanitized accepted `speech.text`, with cancellation
IDs; future STT should drive Listening activity independently. Animation can
subscribe to validated presentation metadata. Neither extension grants controls.

Reproduce with the existing workflows:

```sh
.venv/bin/python tools/fork_validate.py --tests --report /tmp/f25-upstream.json
.venv/bin/python -m pytest -q tests/ai tests/fork
node --test tests/fork/bridge.test.mjs tests/fork/presentation.test.mjs
CHARACTER_BROWSER_REPORT=/tmp/f25-character node tests/fork/character-browser.mjs
FORK_BROWSER_PORT=8790 FORK_OBSERVER_PORT=8798 FORK_BROWSER_REPORT=/tmp/f25-dashboard node tests/fork/browser.mjs
EDGELOOP_LIVE_ACCEPTANCE=1 LIVE_ACCEPTANCE_REPORT=/tmp/f25-live node tests/fork/live-acceptance.mjs
EDGELOOP_LIVE_ACCEPTANCE=1 F25_MATRIX_REPORT=/tmp/f25-matrix.json .venv/bin/python -m tests.fork.evaluate_f25
```

Run live workflows sequentially against the existing 11435 server. They create
isolated fixtures/settings and never restart Ollama or test physical hardware.
