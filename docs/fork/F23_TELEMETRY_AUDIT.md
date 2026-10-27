# F2.3 telemetry audit

Audited against the pinned original EdgeLoop 1.1.3 source, not UI labels.
The starting application tip was `370fe0b` (artwork backup), above live validation
`9c75b0d`, thinking repair `7de7752` and consolidation `b3d7063`.
`backup/f23-pre-grounding-20261027` and the bundle under
`/home/sean/Work/backups/edgeloop-f23-20261027/` preserve this starting point.
Concurrent artwork additions/renames are outside this change and remain untouched.

## Original state to bridge mapping

| Wire / canonical field | Actual original source | Meaning / qualification |
|---|---|---|
| `hr` | `state.sensorHr`, set by `updateEngine()` from the sensor value after `recordHrReading()` | Rounded reported pulse; excludes microphone boost. A default boot value is not a verified BLE sample. Simulator values are synthetic. |
| `devices.simulated_hr`, `hr_source` | `state.simEngaged` | Manual simulator slider, not a physical measurement; its unchanged value does not generate new measurement samples. |
| `devices.ble` | `isBleConnected()` | BLE connection, not proof a valid pulse was received. |
| `devices.hr_ready` | `hardwareReadiness().hrReady` | BLE connected OR simulator engaged; not sample freshness. |
| `hr_recorded_at_ms` | `state.lastHrTimestamp` | Updates only on a usable recorded reading. Capture conservatively waits for a new timestamp after first observing a BLE connection. |
| `hr_live` | read-only `pulseIsLive()` / original HR watchdog | The actual watchdog verdict; reset display flags alone cannot establish a live sample. |
| `resting_bpm` | `minHr` input through original pure `sanitizeHrLimits` | Currently validated configured resting setting, not a measured resting pulse. |
| `single_max_bpm` | `maxHr` input through original pure `sanitizeHrLimits` | Validated single-stimulation configured ceiling, not current BPM or a clinical maximum. |
| `dual_max_bpm` | `dualMaxHr` input with original finite/range/order checks | Independent dual-stimulation setting. Connection roles affect the original working ceiling; the AI does not recompute it. |
| `effective_max` | `state.effectiveMaxHr` | Last engine-computed working ceiling, after original offsets/decay/boost. A derived threshold, not a physiological reading. |
| `pullback` | `state.edgeTriggerHr` | Engine pullback threshold; null stays unknown instead of substituting the working ceiling. |
| `status` | `state.sessionStatus` | `IDLE`, `RUNNING`, `PAUSED`, `RAMPDOWN`. No native STOPPED state. IDLE alone does not prove a stop transition. |
| `seconds` | `state.sessionSeconds` | Engine counter; advances in the RUNNING clock branch. Pause retains it, Stop/Reset zero it. Not wall-clock duration, and not extrapolated by the observer. |
| `experience` | `state.teaseMode` | Selected stroke experience. Does not prove execution, physical motion or goal completion. |
| `active_mode` | `state.activeMode` | Engine's active mode identifier; games can own speeds while borrowing the selected experience's stroke. |
| `goal` | `state.gameMode || 'tease'` | Selected game; null maps to ordinary Tease. Not an achieved outcome. |
| `intensity` | `50 + state.intensityValue` | Displayed 50–150 percent intensity setting; the raw 0–100 slider is not itself that percentage. Not measured physical output. |
| `edges` | `state.edges` | Engine counter incremented on `result.newEdgeTriggered`, excluding settling. Not independent proof of a bodily event. |
| `pauses` | `state.pauses` | Engine counter incremented in `pauseSession()`; resets with session counters. Includes watchdog/user pauses, without inventing intent. |
| `movement.primary` | `state.strokerSpeed = result.primaryPercent` | Computed primary channel value, not motor feedback, confirmed delivery or an actual motion measurement. |
| `movement.secondary` | `state.prostateSpeed = result.secondaryPercent` | Computed secondary channel value; the anatomical legacy variable name is not a measurement of the user. |
| `movement.stroke_min/max` | `state.strokeMin/Max = result.*Percent` | Engine travel envelope; retained on the wire, not presented as physical position feedback. |
| `devices.handy` | `handyConnected` | Driver connection state, not proof the motor is moving or stopped. |
| `devices.intiface` | `isIntifaceConnected()` | Transport connection, not an actuator count or motion feedback. |
| `devices.tcode` | `isTCodeConnected()` | Serial transport connection, not confirmation of an assigned or moving axis. |
| `devices.vacuglide` | `isVacuglideConnected()` | Connection state; disconnection is not confirmation of a successful physical stop. |
| `devices.toy_ready` | `hardwareReadiness().toyReady` | Handy/VacuGlide connected, or connected Intiface with devices, or connected TCode with assigned axes. Not output activity. |
| `safety.signal/no_contact/watchdog_paused/fault` | Original HR status/contact/pause fields plus old bridge's priority fault summary | Signal state is authoritative; `fault` is a projection, not a complete safety diagnosis. Not interpreted as all-system health. |
| `calibration_pass` | `state.calibrationPass` | Selected primary/dual pass or none. Selected calibration is not evidence it ran or completed. |
| `warmup_active/remaining_seconds` | Same read-only formula as `updateWarmupBadge()` | RUNNING and elapsed-from-`warmupOriginSeconds` below configured warm-up duration. UI phase projection, not a second session timer. |
| `ease_down_seconds` | `state.settleSecondsLeft` | Engine ease-down counter. Its cause is not inferred as a physiological event. |
| `rampdown_seconds` | `state.rampdownSecondsLeft` only in RAMPDOWN or a paused rampdown | Otherwise unavailable; the default 45 is not reported as an active phase. |
| `captured_at_ms` | Browser `Date.now()` at read-only projection | Source snapshot time, separate from last sample time and server receipt time. |
| `session_id`, `sequence`, epoch | Capture's observation generation, connection send sequence, authenticated observer epoch | Observation identity/order only; never a second controller or engine session clock. |

The source references are `src/js/state.js`, `app.js` functions
`readHrLimits`, `hardwareReadiness`, `pulseIsLive`, `updateEngine`,
`recordHrReading`, `pauseSession`, `resetSessionCounters`, `stopSession`,
`startOrResumeSession`, `updateWarmupBadge`, and `hr-watchdog.js`.
Only the existing AI observation hook in `app.js` changed: it reads five allowlisted
settings/live-status values using the original pure validator, without calling the
mutating `readHrLimits()` helper. Invalid typed fields are unknown; another invalid
field cannot hide a separately valid setting behind stale last-good values. No calculation, session control or device driver changed.

## Full data path and defects repaired

1. `syncAiObservation` reads state, explicit connection flags and allowlisted
   settings. `Capture.project` constructs a new object without mutating upstream.
   No credentials, raw HR history, hidden targets, device tokens, microphone data,
   schedules or free-form configuration are collected.
2. The bounded latest-state connection transports JSON observation frames over
   authenticated localhost WebSocket. It coalesces events by kind, keeps their
   timestamps/order, drops offline events, uses backpressure, and refreshes only
   the read-only projection while the original clock is paused/idle.
3. The observer's closed Pydantic union validates bounds, enums, extra-field
   rejection and detailed cross-field consistency. Epoch, sequence, retired
   session IDs and capture time prevent replay/old observations becoming live.
4. The observer retains raw validated data for diagnostics, a separate canonical
   fact view for the model, up to 12 distinct timestamped HR samples, 32 observed
   events and 256 deduplication IDs. Reconnection/source changes segment evidence.
5. The Director still owns dialogue policy, history selection, pacing and event
   deduplication. Generated dialogue is never fed into canonical telemetry/events.
   Its legacy flat-state filter cannot strip the canonical data or promote old
   assistant text into facts.
6. Context assembly inserts one current runtime block beside the latest question,
   after historical conversation; the minimal factual policy stays in SYSTEM.
   The Ollama provider prepends the exact selected embedded SYSTEM once. Runtime
   data is authoritative as values, untrusted only as instructions.
7. ModelManager refreshes the snapshot after provider/lifecycle waits, immediately
   before composing an inference and before a correction attempt. Stored history
   contains original user and accepted assistant dialogue, never appended snapshots.

F2.2 problems: device `moving` was inferred from channel percentages; BLE freshness
could be conflated with connection; settings/pause counter were absent; heartbeat
frames were counted as samples; a browser endpoint-difference trend could imply
continuity despite fluctuation, reconnection or session reset; elapsed/phase fields
were easily mistaken for physiological state; raw JSON and historical generated
claims could outvote missing current data. Early F2.3 live testing also demonstrated
that stronger SYSTEM wording alone did not reliably stop stale BPM guesses.

The final design combines structured source facts, per-field freshness, last-turn
placement, inference-only omission of historical telemetry dialogue from current-session
questions, and a narrowly scoped explicit-claim check with one
bounded correction. It does not assert that general language can be fully verified.
