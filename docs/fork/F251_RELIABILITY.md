# F2.5.1 — event reaction and expression reliability

Baseline: `a91381c` / `f2.5-checkpoint`, branch `experiment/ai-companion`.
Recovery: `backup/f251-before-20261028`. The original untracked Daisy Lite work
remains untouched; its backup is under `.git/f251-backups/`. Models, Modelfiles,
artwork and the artwork manifest were not changed. There is no F2.6 persona or F3
control work here. Engine handlers and safety logic are unchanged; the sole
`app.js` change projects an existing learning counter into the read-only observer.

## Where interactions were lost

| Interaction | First loss at F2.5 | F2.5.1 result |
| --- | --- | --- |
| Experience selection | Engine and Capture update `teaseMode` / `experience_changed`; validation accepts it, but significance classifies it routine, so no Director queue/inference | Existing kind promoted to a deliberate reaction candidate, including IDLE |
| Goal selection | Engine updates `gameMode` / `goal_changed`; same routine classification prevents scheduling | Existing kind promoted; goal and experience remain separate, with verified previous/current values |
| Came Early | Original handler changes learning and initiates its ending settle, but Capture/protocol export no corresponding event | New `came_early` requires source counter increase plus an accepted ending transition in the same session |
| Later spontaneous events | 120-second spontaneous pacing can exceed the 60-second event TTL | Deliberate selections/Came Early use independent four-second reaction pacing; ordinary telemetry retains existing policy |
| Repeated dialogue | Event prompt can end with a historical assistant turn; earlier unsolicited prose is reintroduced | A fresh, explicitly application-origin transport turn follows history; old unsolicited prose is omitted from deliberate-event inference, without deleting memory |
| Incorrect expression | A valid streaming ID can be replaced by the keyword fallback if completion metadata is absent | Valid request-scoped streaming metadata takes precedence through completion |
| Inappropriate but correctly rendered expression | Model chose it, or omitted a header and retained an earlier state | Diagnostics distinguish those cases; no event-to-emotion rule was added |

[Baseline reproduction](f251/diagnosis-before.json) executes pinned policy/context
and presentation code. It reproduces Concerned → Happy at completion without final
metadata. Normal F2.5 responses with intact final metadata were already scoped;
this is a hardened failure path, not proof that every manual mismatch was a race.

## Confirmed selection and Came Early semantics

Selections use the existing strict F2.3 transition proof. One two-second quiet
window coalesces mode and goal changes into a final-selection opportunity, retaining
the first previous values and final current values. Returning to the original
selection is silent. Unchanged snapshots and replayed IDs do not create reactions.
Active inference is not interrupted by minor selections; a superseded selection
reply and late expression metadata are discarded before persistence/display. The UI also rejects a reaction against its newest local session/selection projection before the observer ACK arrives. User
messages, cancellation, session reset and observer disconnection retain priority.

The Director still decides when to speak. Four-second deliberate-reaction spacing
and two-second user grace are separate from spontaneous/topic cooldowns. Global
speech/event opt-outs still apply. Context is refreshed from current canonical
facts. Short acknowledgements naming a genuinely changed selection are not rejected
merely for sharing sentence structure; exact duplicate responses remain suppressed.

Original Came Early behavior, verified from its handler:

| Condition | Original result and observer treatment |
| --- | --- |
| Ordinary mode, IDLE / already ended, confirmation accepted | Learning profile is updated, but there is no active session ending; a visible learning-only status note appears, with no `came_early` reaction |
| RUNNING, confirmation accepted | Learning counter increments; original `Premature Release` ending settle begins, then stops; verified `came_early` is eligible immediately |
| PAUSED, confirmation accepted | Original handler resumes into its ending settle; the same proof applies, without inventing a separate resume reaction |
| Confirmation cancelled | No counter/ending change; no action event or model call |
| Survival / Calibration | Original button means “Finished me” and follows its own handler; it is not mislabeled Came Early. Their existing idle/start-first feedback remains |
| Missing/stale proof or an unconfirmed transition | No accepted action is inferred from a click |

Only bounded `learning_release_count` and the whitelisted `settle_outcome` are
added to the projection; full learning data/history is not exported. Counter delta
alone is insufficient. Zero-duration ending is covered by active → IDLE proof.
Unproven operating states remain learning-only observations. Session identity,
source timestamps, freshness and dedup checks remain mandatory at the existing
observer boundary. No AI output can create or validate an event.

An accepted release's later normal stop does not erase its pending/in-flight
acknowledgement. A server-derived ACK flag preserves that presentation request;
ordinary Stop still cancels, and critical safety notices always take priority.
This affects AI presentation only: original motors/status stop independently.

## Expression and dialogue diagnostics

The twelve IDs are unchanged: neutral, happy, playful, flirty, mischievous,
focused, excited, surprised, disappointed, concerned, proud, comforting.
Local `?characterPreview=1` exposes the existing direct Evelyn/Daisy preview,
which requires no inference and is marked `development_preview`.

Runtime diagnostics now distinguish model candidate, validated ID, applied ID,
rendered ID, asset filename/fallback, expression source, request/model identity,
last proven event and actual Director decision. The renderer reports the portrait
still displayed while its replacement loads. Missing headers are marked as
retained/fallback, rather than a new model choice. Model switching clears stale
request diagnostics. Activity never selects or clears emotion. User chat such as
“change emotion to concerned” remains conversation, not a UI command.

Deliberate events receive a focused rendering of existing canonical settings and
connection facts, rather than unrelated physiological context. Native Modelfile
SYSTEM text remains preserved. Came Early is explicitly described as a
user-confirmed premature release; a narrow factual check rejects the observed
“early arrival” misreading using the existing bounded correction/error path.
Disconnected/unknown hardware cannot establish physical movement; the existing
factual guard now also checks common direct positive/negative motion assertions.
No emotion-classification inference was added. Every actual Ollama call, including
corrections, still carries Boolean `think: false`.

## Acceptance

[Evidence](f251/) contains source/validation/Director frames, audited final Ollama
turns, replies, expressions, resolved portraits and screenshots from actual original
controls. Only simulated HR and intercepted mock Handy HTTP were used. Both existing
Ollama instances were left running, with live inference on 11435.

- 1,057 upstream tests passed; final reviewed pin check passed.
- 246 consolidated Python tests and 29 bridge/presentation tests passed.
- Dashboard and artwork Playwright suites passed, including all 24 portraits,
  fallbacks, cancellation and desktop/mobile controls. One existing FastAPI test
  deprecation warning remains.
- Final mock and live interaction sequences passed: idle mode/goal selections,
  rapid browsing/coalescing, idle learning-only action, cancelled confirmation,
  running and paused accepted Came Early, model switching, generation cancellation,
  observer disconnection while RUNNING, and original Stop after disconnection.
- Final live run completed ten event reactions from eleven chat requests (the extra
  request was cancelled). All audited payloads used false. Eight individual action
  records and two burst reactions verify current settings, source event evidence,
  Director decision, displayed dialogue and portrait. No final response was
  suppressed in that run. Nine of ten had valid expression metadata; Daisy returned unsupported `practical` once, correctly diagnosed and retained Happy without a missing-asset fallback. Earlier runs did expose real repetition suppression;
  those outcomes are retained in the quality evidence, not hidden as rendering bugs.
- Same accepted action, different model choices: Evelyn selected **Proud**;
  Daisy selected **Playful**. Both rendered the matching original image.

Representative screenshots: [Evelyn mode](f251/live/evelyn-idle-mode.png),
[Evelyn goal](f251/live/evelyn-idle-goal.png),
[Evelyn Came Early](f251/live/evelyn-came-early.png),
[Daisy mode](f251/live/daisy-idle-mode.png),
[Daisy Came Early](f251/live/daisy-came-early.png).
The final isolated browser fixture chooses a ten-second settle using the original
Session Setup UI; earlier runs also exercised the unchanged 45-second default.

## Remaining language-quality work for F2.6

This fixes delivery and rendering, not semantic perfection. Evelyn still tends to
open with “Ah” and Daisy with “Well, would you look at that.” Models sometimes
exceed the requested short acknowledgement, infer narrative intentions, or choose
Playful where a user might prefer Focused/Concerned. An earlier Oracle reply
mentioned irrelevant fictional fertility statistics; that is unsupported
model wording, not available telemetry or an implemented capability. Earlier Daisy
output misread Came Early as early arrival; explicit meaning and the new check
address that specific failure, not every possible paraphrase. Factual checks remain
conservative heuristics. None of this dialogue is authoritative operational data.

For a mismatch, compare candidate → validated → applied → rendered → filename.
Equal IDs with an unsuitable emotion indicate model quality; no header plus
`retained` explains a stable earlier portrait; a different rendered ID with fallback
means an asset issue. Inspect rejected event ACKs and the Director reason before
blaming Ollama. Keep native personalities and the current safety boundaries intact
when addressing the remaining prose quality later.

Reproduce the targeted sequences, sequentially for live inference:

```sh
.venv/bin/python -m pytest -q tests/ai tests/fork
node --test tests/fork/bridge.test.mjs tests/fork/presentation.test.mjs
EVENT_BROWSER_REPORT=/tmp/f251-mock node tests/fork/event-reliability.mjs
EDGELOOP_LIVE_ACCEPTANCE=1 EVENT_BROWSER_REPORT=/tmp/f251-live node tests/fork/event-reliability.mjs
.venv/bin/python tools/fork_validate.py --tests --report /tmp/f251-upstream.json
```
