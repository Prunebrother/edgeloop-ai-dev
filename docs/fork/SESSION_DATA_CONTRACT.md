# Canonical session data contract — F2.3

## Transport compatibility and validation

The existing v1 observation/chat/auth protocol remains closed and read-only.
`Snapshot.details` is an optional, closed `ProjectionDetails` object containing
capture/sample timestamps, an optional original-watchdog live verdict, resting/
single/dual validated settings, pauses and bounded phase values. Old v1 clients
remain readable; facts absent from their projection stay unknown, and a legacy BLE
frame without a measurement timestamp cannot establish a current reading or trend.
`pullback` now accepts null because an uncomputed threshold must stay unknown.

New read-only event kinds distinguish experience, goal, intensity and threshold
changes. Optional event capture time/session ID allow cross-session and stale event
rejection. No arbitrary settings, commands, tools, URLs or free-text sources were
added. Authentication, origin restrictions, message size limits, rate limiting,
closed discriminators, numeric bounds and extra-field rejection remain enforced.

Detailed frames reject future measurement times, a reading without a ready source,
readiness without a declared BLE/simulator source, toy readiness without a connection,
and an active warm-up outside RUNNING. Same-generation counter regressions while
active are rejected. Unsupported/inconsistent event assertions are not promoted to
canonical history or sent to Conversation Director pacing. The observer does not validate physiological truth independently
of the authenticated original browser; it never talks to physical devices.

## Canonical facts

`companion_ai.grounding.SessionFacts` is the validated model-facing contract:

- `contract = edgeloop.session-facts.v1`
- observation session ID, sequence, capture time, age and current flag
- a bounded map of `Fact` objects
- at most six recent, same-segment `HistoricalEvent` records
- trend sample count and span

Each Fact contains `value`, `unit`, `kind`, original `source`, `known`, `current`,
`observed_at_ms` and `reason`. Kinds distinguish measurement, setting, status,
derivation and computed engine value. Unknown is null, never a fabricated zero.
Historical known values can remain in diagnostic facts with `current=false`, but
the model renderer suppresses their numbers. Physical motion is explicitly unknown
because this read-only bridge does not collect hardware feedback. Connection,
readiness, channel computation and session status are independent facts.

Example: a connected simulator at 98 BPM gives a known synthetic value; a BLE
connection with no verified sample gives unknown HR; an old BLE sample gives a
known last value but not a current measurement. A resting setting of 70 BPM is a
setting even when there is no sensor. A disconnected Handy does not establish
whether its motor physically stopped.

## Time, sampling and history

Transport freshness is at most five seconds including source-capture age, not
just receipt age. Capture more than one second in the future or regressing within
an epoch is rejected. This relies on browser and backend using the same local host
clock; a large clock jump is handled conservatively by losing freshness, not by
inventing a value. No observer clock advances session time or resets engine counters.

BLE currentness also requires an original live/OK/contact verdict and a verified
sample no older than five seconds. The manual simulator's held slider value remains
current when freshly projected; repeating that projection is not a new sample.

Trend evidence: maximum 12 distinct measurement timestamps in 15 seconds, at least
four samples spanning three seconds, with no gap over five seconds. A rise/fall
needs a monotonic direction and at least three BPM net change; steady needs at most
two BPM range. Fluctuating or insufficient evidence is unknown. No emotions or
intent are inferred. Transport gaps, source changes and new observation sessions
clear/segment evidence; a pre-segment sample cannot create post-reconnect continuity.
The old wire trend is not treated as evidence by the canonical view.

Event history retains at most 32 validated observed changes; the model sees only
the latest six within 120 seconds. Up to 256 IDs prevent duplicate processing.
Timestamped events keep capture ordering and provenance. Engine edge increments
are not claimed as independently measured bodily events. No event is manufactured
from model dialogue, a selected mode, a working threshold or a single HR sample.

## Model construction and correction

The exact installed Modelfile SYSTEM remains first, verbatim, once. The app adds
only a general factual/read-only policy, not tone, names, lore or a personality.
There is one current runtime block per request, immediately before the separately
marked user question; events/revisions receive the corresponding data block without
posing as genuine user dialogue. Each model retains its original conversation store.

Current facts supersede historical dialogue. When the user asks about the current session, historical telemetry dialogue is
omitted from that inference only: neither old assistant claims nor old user reports
become current sensor evidence. Personal dialogue and all stored messages remain
intact; explicit questions about previous dialogue still retain that history. Conservative context budgeting still trims old inference history without
truncating the current facts or silently enlarging the model's supported context.

The explicit-claim check covers unsupported numeric/word-form BPM, obvious wrong
current BPM, sensor-source contradictions, direct connection/status/counter claims,
unitless numeric pulse guesses when readings are missing, strong unsupported trend claims and explicit unverified physical-motion/AI-control
claims. It is not a general semantic verifier. Clear historical references may be
acknowledged as dialogue, without being promoted to live measurements.

Current facts are refreshed after generation as well as before inference, so a slow
completion cannot reuse expired readings without a factual recheck.

One factual correction is allowed within the existing generation deadline, with a
stream reset and the same embedded SYSTEM. A still-conflicting reply is not saved;
the UI removes the rejected final draft and displays an error. Early streamed tokens
are provisional and may briefly contain a false claim before correction; token-level
truthfulness is not promised. No fabricated fallback dialogue is substituted.
Original stop/safety handling remains independent and immediate.
