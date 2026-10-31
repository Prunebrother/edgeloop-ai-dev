# F2.8.5 — Director initiative, novelty and event deduplication

## Pre-change audit

Starting HEAD `710b81e`, branch `experiment/ai-companion`, with existing uncommitted memory/Nova work preserved. Ownership is limited to Director orchestration, context selection, configuration and diagnostics. Character sources, knowledge/lore, art, model definitions, model sampling and response/output budgets are excluded.

- `ConversationService.pump()` is the existing sole scheduling loop. The observer maintenance loop calls it every 250 ms while observations are fresh. User messages call `request()` directly and cancel previous generation. `ModelManager.lifecycle_lock` already serializes provider operations. Curator work is cancelled by incoming user/events.
- Original hardware stopping is independent of the observer. `safety()` immediately publishes a deterministic notice and cancels commentary, preserving the accepted completion exception. No model is involved in physical stopping.
- SpeechPolicy defaults: 45 s speech interval, 60 s per-event cooldown, 15 s user grace, 60 s event TTL, queue limit eight. Reactive selections/completions bypass those general pacing gates.
- Director defaults: 120 s spontaneous interval, 30 s user-idle gate, 90 s topic protection, 90 s signature deduplication, 30 s aggregation, max two unsolicited replies. Reactive changes have 2 s debounce, 2 s user grace and 4 s reaction spacing. Categories have independent cooldowns (physiology 180 s, edge/session 120 s, device 90 s, tool 60 s).
- EventIntelligence adds detector and commentary cooldowns (configuration/session defaults 5 s), hysteresis and character relevance. Its quiet detector requires 120 s without significant activity and considers one scope/revision only.
- BrowserObservation validates transitions, source timestamps, sequence and session identity before scheduling. Its seen-ID set resets on reconnect. The server also has a five-minute transport seen set. Director signatures expire after 90 s and include new IDs/source timestamps, so they are not a durable occurrence acknowledgment ledger.
- Pending events are coalesced by kind, selections by debounce. Model/session/reset transitions cancel pending work. Only start/resume and selected-setting mismatches are explicitly invalidated before generation; ordinary stale events can otherwise survive until TTL.
- Idle narrative continuation requires an opted-in story, a choice/commitment, no unanswered thread, a new narrative revision, Director gates AND the separate quiet detector. Thus general conversation cannot independently initiate and a story normally gets one continuation per user revision.
- Existing repetition checks compare up to 12 responses, phrases and questions. One bounded repair inference is optional. Broad user-topic protection is not an autonomous topic/intent cooldown.
- Context Compiler selects current canonical facts independently of narrative data. Event-focused compilation can append another historical event; acknowledgments come only from the last four narrative event references and disappear when narrative memory is disabled/reset. This creates opportunities to reinterpret an older event.
- Director drawer exposes one service-wide proactive toggle, queue/cooldown/status diagnostics. Event Intelligence exposes a shared proactive interval, detector thresholds/cooldowns and per-character category relevance. Director.json is global. No UI control exists for independent idle frequency, idle cooldown or autonomous topic cooldown.

Implementation and measured validation follow below after the audit; no service restart is part of this work.

## Implemented behavior

A frozen `710b81e` regression reproduces two defects: the same event becomes eligible after 91 seconds, and a new envelope ID for the same structured occurrence bypasses signature deduplication. Both are now rejected. No playtest transcript was supplied for this milestone, so these are demonstrated scheduling paths, not a claim that every reported narrative repetition had one cause.

- The existing Director owns a bounded occurrence ledger (1,024 identity keys, approximately 512 two-key occurrences). It uses session + original ID and, where available, a validated transition key. Edge counters and five-minute milestone boundaries identify their occurrences; setting transitions use source time and before/after values. Anonymous legacy observations retain their existing short signature window. A genuine later transition/counter remains eligible. Safety notices bypass model-commentary deduplication.
- Receipt, coalescing, dispatch, acknowledgment, cancellation and failures are diagnostic stages. A repeated occurrence is not automatically retried after failed/cancelled generation. A storyline reset or memory disablement does not erase this operational ledger. It is intentionally not a new persistent telemetry store.
- All queued event kinds are checked against their current session/selection/observer connection epoch before dispatch and before display. Reconnects invalidate old generation even when an adapter returns late. Idle contributions are stopped on pause/stop; direct chat remains available. Accepted completion commentary keeps its existing post-stop exception. A fresh deliberate settings action while already idle remains eligible; a settings reaction queued while running becomes obsolete when that session stops.
- Experimental idle planning runs inside the existing `pump()`, not a second scheduler. It selects an intent/reference and leaves all prose to the selected model: `narrative_development`, `dialogue_follow_up`, `memory_recall`, `character_curiosity`, or `contextual_observation`. Meaningful session events retain their separate verified-event path. Stories require existing welcome/continuity; curiosity can be eligible without a structured story when the experiment is explicitly enabled. Privacy-disabled memory cannot supply follow-ups, fictional facts or recalled details.
- Topic keys are bounded to 32 per model, recent intent history to 12. Least-recently-used eligible intents rotate; cooldowns apply to reference/topic keys. Source-backed facts retain their existing provenance, scope and epoch. There is no additional LLM classification/consolidation call for scheduling. Existing optional bounded repetition repair remains unchanged.
- Lifecycle commentary has priority over ordinary queued events and uses reaction pacing instead of the general event interval. Model commentary still yields to direct user dialogue; deterministic safety/lifecycle notices are immediate. Queued user/model work blocks idle dispatch, and incoming direct chat cancels active automatic commentary before waiting on discovery. New significant events can cancel an active idle turn. They do not preempt a direct user generation. Original safety/lifecycle handling remains immediate and independent of AI. New idle turns do not stamp event/category cooldowns, avoiding accidental starvation of later events. Existing speech/detector/category gates still apply and may expire a queued candidate rather than narrate it late.
- Explicit quiet/break requests suppress autonomous contributions across model switches until an explicit resume request. Direct questions still receive direct replies while muted. Narrative mentions or quotations about taking a break are not mute commands. Pending commentary is discarded rather than replayed after quiet mode ends.

## Source contract and response length

The compiler receives a `director_opportunity` with intent, topic key, optional memory reference and session identity. It is labelled **scheduling data, not telemetry or a user statement**. Idle focus selects compact current status and relevant dialogue/fiction; detailed sensors/settings and historical events are not automatically primed. Memory recall resolves an existing reference through the normal scope/epoch-aware retrieval path.

Known event acknowledgments are excluded from idle history and generic event-only development excerpts, without deleting stored transcripts or facts. Recorded source metadata identifies these replies; exact excerpt membership is a compatibility projection for existing untagged development stores, not event-identity matching. Genuine dialogue and established personal facts/commitments remain available. Candidate selection reuses existing memory significance so routine detours are not automatically chosen as meaningful recollections. Context Intelligence reports `idle_context_exclusions` and per-fact exclusion reasons.

Event-focused compilation supplies only the named verified trigger. It does not append a second historical event. The Director acknowledgment ledger supplements narrative references, so narrative reset/disablement does not turn an old event into fresh evidence. Explicit user questions about earlier events can still receive clearly labelled historical evidence, including an `already_acknowledged` marker; they are not fresh automatic reactions. Canonical facts, user reports, historical journal data and fictional context retain their separate existing labels and validation.

No model definition, native persona, backstory, lore, shared character knowledge, art or expression mapping was changed for F2.8.5. Prior uncommitted Nova/artwork and memory changes remain present in the working tree. No response-length setting, sampling preset, token/output budget or model size was reduced. New initiative instructions impose no brevity requirement. Normal inference remains `think:false`, with the existing provider lifecycle lock serializing inference. No hardware tools or control pathway were added.

## Settings and migration

The existing Director drawer now exposes:

| Control | Default | Scope/meaning |
| --- | --- | --- |
| Enable proactive dialogue | Existing value; normally on | Master automatic commentary switch; safety notices and direct replies are independent |
| Experimental idle initiative | **Off** | Opt in per selected model; preserves existing behavior until enabled |
| Initiative interval | **50 s** | Minimum quiet/attempt spacing; suggested initial range 40–60 s |
| Idle response cooldown | **40 s** | Minimum delay after a delivered idle reply finishes |
| Event reaction cooldown | Existing **4 s** | Existing reaction pacing; completions retain their exception, and other speech/detector/category gates remain independent |
| Topic repetition cooldown | **180 s** | Time before revisiting the same autonomous reference/topic |
| Consecutive unsolicited replies | Existing **2**, configurable 1–4 | Bounds uninvited continuation; significant verified events retain priority |

Intervals are eligibility floors, not guaranteed output times. Reading/busy time, user activity, typing, pending events, observation freshness, quiet mode, topic cooldowns, the unsolicited limit or model-selected silence may prevent a turn. Enabling the experiment during an already quiet period can make the next check eligible immediately.

`director.json` remains the legacy service default. Old protocol messages containing only `proactive_enabled` remain valid. New model-targeted settings are validated and atomically stored as overrides in `director-models.json`, keyed by the same full provider/endpoint/model scope as existing dialogue. Model switching/restoring does not copy settings to another character. Corrupt model settings are preserved and diagnosed; defaults apply without overwriting the file. The UI keeps its legacy toggle compatible with an older running observer and hides unsupported new controls until the updated observer is loaded.

Event Intelligence's previous proactive interval is explicitly labelled **Event commentary / legacy initiative interval**. Its quiet detector continues to govern the legacy path; diagnostics identify the experimental selector when that alternative is active. No duplicate sensor detector or second session controller is introduced.

The drawer shows current-model intent history, quiet state, pending commentary, cooldowns and a bounded decision trail with kind/ID/topic references. Backend counts distinguish duplicate occurrences, queue expiry/scope rejection, topic candidate suppression and response rejection. Deferral counters count **reason transitions**, not every 250-ms poll and not unique messages. No raw conversation text is added to scheduling logs.

## Deterministic 15-minute benchmark

Run:

```sh
PYTHONPATH=. .venv/bin/python -m tests.fork.director_session_benchmark --output /tmp/f285-session.json
```

This uses the real observer, Director, queue, Context Compiler, response validation and provider protocol with mocked Ollama responses. It includes running heartbeats, repeated and genuinely new settings/edge events, a milestone, pause/resume, explicit quiet/resume, reconnect, duplicate backfills and stop at second 840. It uses four consecutive unsolicited replies for comparison; normal defaults remain two. The fixture deliberately repeats candidates and reuses a finite response corpus to stress the existing repetition guard. **It is not a live-model creativity evaluation.**

Both arms use the repaired scheduler; they differ only in the experimental idle setting. Thus this comparison measures initiative behavior, not a pre-fix deduplication benchmark.

| Metric | Experimental off | Experimental on |
| --- | ---: | ---: |
| Autonomous inference opportunities | 7 | 14 |
| Delivered autonomous messages | 6 | 7 |
| Average delivered-response spacing | 122.00 s | 58.67 s |
| Replayed events suppressed | 9 | 9 |
| Duplicate accepted event IDs | 0 | 0 |
| Topic candidate evaluations suppressed | 0 | 8 |
| Repetitive candidates rejected | 1/7 (14.3%) | 7/14 (50.0%) |
| Queue candidates expired/out of scope | 1 | 1 |
| Provider calls, including direct replies | 13 | 20 |
| Generation errors | 0 | 0 |
| Maximum parallel inference | 1 | 1 |
| Automatic messages after stop | 0 | 0 |

Delivered trigger categories: off = edge 1, experience changes 2, resumed session 1, legacy narrative 2; on = narrative development 1, dialogue follow-up 1, memory recall 1, edge 1, experience changes 2, resumed session 1. The experimental arm also schedules contextual observation and curiosity; their scripted candidates are rejected by the repetition guard in this fixture. All five intents are therefore tested at scheduling, not all demonstrated as successful live prose. The higher rejection rate is reported rather than described as a narrative-quality improvement.

The benchmark exposes full per-trigger request counts, deferral transitions, accepted IDs and estimates in its JSON. All provider requests have `think:false`, no tools, and the unchanged 2,048-token fixture output allowance. Compilation/900 virtual seconds take under one second of host wall time in this fixture, excluding real model inference. Prompt and inference latency under a live model are not measured here.

## Regression validation and limits

**705 Python tests pass**, with three known socket-dependent cases deselected in this restricted environment; **63 companion JavaScript tests pass**; **1,057 upstream tests pass**, and the original-file verification passes. As in the preceding memory work, in-process Python asynchronous tests used a test-process-only selector polling shim because this environment denies asyncio self-pipe writes; no production asyncio behavior was changed. Compact results are in [f285-session-benchmark.json](f285-session-benchmark.json). Full logs: `/tmp/f285-python-final.log`, `/tmp/f285-js-final.log`, `/tmp/f285-upstream.json`; full synthetic trace: `/tmp/f285-session-final.json`. Regression coverage includes checkpoint reproduction; same-ID and alias/transition deduplication; genuine later events; pause/resume/milestones/derived-event families; idle without new significant telemetry; intent rotation and bounded topic state; user and major-event preemption; silent/fictional-quiet distinction; stop/reconnect invalidation; source-backed recall and privacy disablement; scoped settings, migration and corruption handling; explicit historical answers; hardware-tool absence; output budget and `think:false`; and provider serialization under interruption.

Two earlier fixtures were updated to supply a fresh running session/matching current selection instead of asking an obsolete event to enter inference. The earlier blanket acknowledgment-history assertion now verifies the intended distinction: direct historical questions may receive old evidence, but the same occurrence cannot become a fresh automatic trigger.

The updated Playwright Director workflow exercises all new controls, saves and verifies their values through the isolated backend, and restores the experiment to off before unrelated scenarios. Its UI/backend ports are checked before launch, can be overridden, and inherited desktop pairing credentials are removed from test children. Cleanup targets only owned child handles. This environment rejects the first port probe with `listen EPERM 127.0.0.1:8850`, so browser rendering/interaction is **blocked, not passed**. No live service was restarted or replaced. Report: `/tmp/f285-browser-final/report.json`; log: `/tmp/f285-browser-final.log`.

Occurrence retention is bounded and in-process. It is not an indefinitely persistent acknowledgment archive; older entries can age out through capacity, and observer restarts rely on existing source freshness/transition validation. New envelope deduplication needs a stable source occurrence; anonymous legacy events cannot be perfectly distinguished without inventing identity. Topic fingerprints and lexical repetition checks are approximate and cannot guarantee semantic novelty. Default unsolicited limits still bound idle conversation. Native model responsiveness and subjective narrative quality require live review; no live Ollama evaluation or physical hardware test was performed.

## Live verification

When convenient, manually load the updated observer with the normal launcher, retaining the current data directory and Ollama endpoint, then reload the UI. Do not start a second observer on an occupied port. No restart is automated here.

1. Select the desired existing model, open **Conversation Director**, keep proactive dialogue enabled, enable **Experimental idle initiative**, and save 50 s interval / 40 s idle cooldown / 180 s topic cooldown. Optionally choose four consecutive replies for a more active trial. Repeat configuration separately for another model to verify scope isolation.
2. During a user-controlled session with fresh observer heartbeats, converse normally and leave a quiet period. Inspect intent/topic IDs and reasons for skipped turns. Check that new dialogue does not repeatedly retell the latest mode or edge change. Do not expect a fixed reply every 50 seconds.
3. Change a setting through the original controls, cause only safe/user-controlled milestones, and reconnect the observer. Confirm one eligible reaction per verified occurrence; old events must not replay. A genuinely new change must remain eligible.
4. Send a direct question during an idle generation. It should take priority. Say **“Give me a break”** and confirm autonomous conversation stops; direct questions still work. **“You can talk again”** explicitly resumes it. Pause and chat, then stop through the original UI: idle turns must stop and pending ordinary events must be discarded. A verified accepted completion may still receive its one completion acknowledgment.
5. Review actual wording, recurrence, latency and prompt-token diagnostics with Nova/Evelyn or any other existing character. Personas and response length should remain native. Leave the experiment off if live costs/novelty are unsatisfactory.

Other local checks:

```sh
.venv/bin/python -m pytest -q tests/ai tests/fork
node --test --test-isolation=none --test-reporter=tap tests/fork/*.test.mjs
.venv/bin/python tools/fork_validate.py --tests --report /tmp/f285-upstream.json
NARRATIVE_BROWSER_REPORT=/tmp/f285-browser node tests/fork/character-menus-browser.mjs
```

For occupied test ports, set `EDGELOOP_MENU_UI_PORT` and `EDGELOOP_MENU_AI_PORT` to unused values. The runner refuses to attach to an existing port owner. No pairing tokens or actual conversation transcripts are written to this report.
