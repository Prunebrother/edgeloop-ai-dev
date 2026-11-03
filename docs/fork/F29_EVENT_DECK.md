# Director 2.0 Event Deck: live scheduling behaviour

`ConversationService` deals these cards live when a model's deck is enabled. The deck is off by default. It is enabled per exact model scope in the data directory's
`deck-settings.json`, which is read when a model is activated:

```json
{"schema_version": 1, "models": {"<sha256 of provider:endpoint:model>": {"enabled": true, "countdown_seconds": 10}}}
```

`simulated_session` (default `false`) may be added for a test run. It tells the model that the listed
session values are simulated and shouldn't be described that way. A heart-rate card keeps its own label
instead. The flag is never inferred, so it can't relabel a real session.

Director 2.0 is the only proactive dialogue scheduler. The legacy idle selector, narrative continuation and
legacy event reactions are retired. With the flag off, a model keeps ordinary conversation, safety notices and the
acknowledgement of the user's own experience or goal selection, but has no other unsolicited commentary: events
still go through detection, Event Intelligence, the occurrence ledger, Story Memory and recent context, and are
recorded as `context_only:no_card_dealer`. No Arrival is armed and no definition or history is read. Saved Director
settings that still contain the retired pacing fields (`experimental_idle_enabled`, `idle_interval_seconds`, …)
load normally and those fields are ignored. The Director's fidelity checks are scoped to card turns
(`violations(..., card=True)`), so user turns and selection acknowledgements keep the checks they had before the
deck. `tests/ai/test_premerge_corrections.py` pins the examples.

## Starter cards (`config/event-deck.json`)

Cards state an intention, never fixed dialogue. Normal cards are drawn from one shuffled sequential
deck per model and session, unweighted. All of them use `memory: none`.

| Group | Cards | Available when |
|---|---|---|
| Opening / closing | `opening`, `closing` | Always; closing has the highest priority |
| Edge count | `edge-count-first`, `edge-count-many` | 1 to 4 edges; 5 or more edges |
| Duration | `duration-settling`, `duration-long` | 5 to 20 minutes; 20 minutes or more |
| HR trend | `hr-rising`, `hr-falling`, `hr-steady` | Current heart rate with that verified trend |
| Encouragement | `encouragement-warm`, `encouragement-pace` | Running |
| Performance | `performance-edges`, `performance-time` | 2 or more edges; 10 minutes or more |
| Playful challenge | `challenge-wager`, `challenge-imagination` | Running |
| Recovery | `recovery-easing`, `recovery-winding-down` | 1 or more edges with a falling trend; ramping down |
| General | `general-remark`, `general-own-interest`, `general-curiosity` | Running |
| Follow-up | `general-follow-up` | Running, and the participant has said something this session |
| Nova only | `nova-curiosity`, `nova-challenge` | Running |
| Evelyn only | `evelyn-observation-edges`, `evelyn-observation-trend` | 1 or more edges; current heart rate with a verified trend |
| Daisy only | `daisy-production`, `daisy-encouragement` | 1 or more edges; running |
| Celeste only | `celeste-evaluation`, `celeste-personal` | 1 or more edges; running |
| Missions | `edges-3-reached`, `edges-7-reached`, `edges-10-reached` | Engine edge counter reaches 3, 7, 10 |

A card that isn't available stays in the deck and is passed over until it is, so a session with no
sensor simply never draws an HR card. The rule also picks the verified facts the model receives: edge
rules supply the edge count, time rules the running time and HR rules the current reading and trend.

Missions use the engine counter rather than events, so they continue with Event Intelligence off. HR
cards obey Event Intelligence and the per-character physiology setting. They are normal cards using
the observer's verified trend, so a simulated source qualifies and the brief tells the model to say so.

Current limits:

- **Numbers are checked by pattern, not understood.** See "Session measurements" below.
- **Restart:** deck state is in memory. See "Restart" below for what that does and doesn't cover.

## What the model receives on a card turn

The Director calculates and the companion reacts. `card_instruction` in `context_compiler.py` sends one short
briefing: `Occasion` (from the card's `occasion` field), `Verified facts` (worked out in Python and stated as
finished sentences), `Task` (the card's brief), then short guidance on form. Card IDs, intents, lanes, scheduling
diagnostics and JSON stay out of the model-facing text. The experience and goal labels aren't sent on Arrival,
Closing or mission cards. User turns and legacy event reactions keep their existing prompt.

- **Arrival:** how long ago the last session ended and how long it ran are separate lines, and the first says it
  is not the second. An unknown length is stated as unknown, with the instruction to say nothing about it.
- **Mission:** the milestone, the verified count and "Session status: still running" are stated outright. There
  is no ordinal such as "first milestone", which the model read as "first edge". The compiled facts fixed that
  miscount, so no check looks for it.
- **Closing:** this session, the previous session, a `Verified difference` sentence and how the session ended
  arrive already compared. The difference line says it is the gap between the sessions, not how long either ran. If a length is unknown, the facts say so and no time difference is given.
- **Opening:** `ConversationService.relationship` maps the Journal lookup to `returning` (`found`), `first`
  (`none`) or `unknown` (everything else). Only `first` is asked to introduce itself, and only a known `returning` companion is checked for reintroducing itself. No record figures or earlier
  transcript reach an opening through this. An opening is not told whether an Arrival has just greeted the participant.
- **Story direction:** it can shape the reaction but is not given as a self-description, and verified facts stay
  as listed. It reaches Arrival and Closing cards only.
- **Evidence:** the real-model harness is `docs/fork/f29-smoke/accuracy.py`, with its independent audit in `audit.py`, on synthetic Journal data. The reviewed runs delivered 723 of 724 turns and, after the rules were simplified, 148 of 148. Their raw dialogue logs aren't kept in the repository.
- **Settings:** a line saying the companion selected a mode or setting (`fidelity:read_only_control_claim`) gets
  one correction, then suppression. Fictional dominance such as "you will obey" is not affected.

- **Form:** one or two sentences of about 15 to 35 words; missions and the closing may run slightly longer.
  This is guidance to the model. Nothing is truncated afterwards, so a long reply stays long.
- **Questions:** only a challenge card, or a card following a real exchange, may ask one. Otherwise the
  instruction asks for a statement, because the participant may not reply.
- **Variety:** each turn gets one of four rotating opening styles. Earlier lines are never quoted to the
  model, because in a real-model run it copied the quoted lines. A draft that reopens like, or shares four
  words in a row with, one of the last 4 commentary lines gets one regeneration. If the retry still repeats
  wording it's delivered anyway, unless the existing repetition check rejects it.
- **Grounding:** the participant's feelings, past, family and character may be offered only as a guess or a
  tease. Fiction may appear as a habit, opinion, wish or what-if, not as something that just happened. This is
  guidance only, except that a named time of day earns one regeneration. A line that still names one is delivered.
- **Test language:** wording such as "test run" or "edge counter" on a card turn gets one correction, then
  suppression (`fidelity:test_language`), with no error shown. Calling a heart rate simulated stays allowed, and
  user turns aren't checked.
- **Missions and endings:** reaching a milestone completes an objective, not the session, and the mission brief
  and instruction both say so. A mission draft claiming the session ended gets one correction, then suppression
  (`fidelity:premature_session_end`). Only the closing card receives the finalized result, and it may announce
  the ending. This is a pattern check on mission cards only, so normal cards aren't covered.
- **Sources:** measurements, the participant's own report and Story Memory fiction are labelled separately.
  A simulator's heart rate is always marked SIMULATED.

`ConversationService.card_history` projects what a card sees: the last 4 messages from this session that
belong to a real exchange (a user message or a reply to one). Earlier commentary isn't replayed, so a card
can't continue its own monologue or copy an old count from it. Stored transcripts aren't changed. A retained
exchange can still contain an old figure, so the instruction says only the listed values are current.

An Arrival sees no transcript in any Journal state. While IDLE the current session ID is the previous session's,
so its transcript is that session's record, and only the lookup dealt to the card may speak for it. Story details
that state a session's performance (edges, running time, operational figures) are left out of an Arrival for the
same reason; other story memory stays. Both are prompt projections: stored history and user turns are unaffected.

Limit: this is instruction, not enforcement. Length, questions and word choice depend on the model.

### Expression headers

The system prompt carries the full `[[expression:ID]]` contract on every turn. A card prompt also opens with
a one-line reminder of it. Without that line, replaying the same logged Daisy prompts on the real model gave
3 of 24 canonical headers, mostly `[[happy:Daisy]]` or `[[happy:3]]`; with it, 24 of 24. The reminder is
sent only when headers are enabled, and only on card turns, so other prompts are unchanged.

On card turns only (`ExpressionStream(card=True)`), `ExpressionStream` removes malformed tags before anything is
shown or stored: anything with a colon inside `[[ ]]`, and, where a header belongs at the start of the reply, a bare
`[[happy]]` and one-bracket forms such as `[happy]` or `[expression:happy]`. Mid-line, only an unmistakable tag
(`[expression:happy]`, `[happy:Daisy]`) is removed. These are never translated into an expression, so the turn uses
the existing fallback (`expression_source: fallback`). Ordinary brackets stay visible, including an expression word
used as prose: "He looked [proud] of it." User turns, legacy reactions and `clean_dialogue` keep their earlier
behaviour whether the Director is on or off.

Limit: the reminder fixes the format, not the range of moods. This model mostly picks `happy`, then `proud`
and `playful`, as it did before the card prompt was shortened.

## Session measurements

`fidelity.py` checks edge counts, pause counts and running time in common wording: "you've reached nine
edges", "that's your ninth edge", "edged nine times", "nine trips to the edge", "twenty minutes in",
"it's been half an hour". This applies to card turns only. A person's conversation can say "we've been walking
for two hours through the ruins" and keeps the narrower checks of the normal pipeline, such as "the edge count is 9".

- **What a claim is checked against:** the current counters; what this generation was told, so a counter
  advancing mid-reply doesn't reject a correct line; the final session result on a closing, after counters
  reset; and completed sessions when idle or when a past session is named.
- **Not treated as claims:** goals and wagers, hypotheticals, fiction, other people, negations, questions,
  anything attributed to the user, and time spent on some other named activity ("we've been walking for").
- **Rounding:** "about", "over" and "under" are honoured. Running time allows 20 seconds, 90 seconds or 15
  minutes for a figure in seconds, minutes or hours.
- **A failed check:** one regeneration with a correction, then nothing is delivered, saved or added to
  Story Memory. This is a suppression, not a failure: the deck records `suppressed` with reason
  `fidelity:<codes>`, the Director logs `deck_card_rejected`, and `response_suppressed` is published with no
  `conversation_error`. The card follows the existing bounded retry lifecycle.
- **Still an error:** a user turn or legacy event reaction rejected by the normal pipeline's own checks, and any
  genuine inference failure, including on a card.

Limits: this is pattern matching. A figure with no noun in its sentence ("you're at nine now") isn't
recognised. Word-form durations about past sessions and personal bests aren't checked. Intensity, speed
and invented measurements of other kinds aren't covered by this check.

## Simulated heart rate

HR cards still play from a simulator. On a card turn, its readings must not be presented as a real body or a
physical sensor: "your real pulse", "an authenticated reading", "the sensor reads 98", "I can feel your pulse" and
"your heart is pounding" are rejected while the source is the simulator. Labelled wording passes ("the
simulated heart rate is rising"), as does doubt or contrast ("rather than your actual pulse"). A real BLE
source is unaffected, and physiology preferences and Event Intelligence are unchanged.

## Restart

Nothing new is stored. The Director's occurrence ledger, deck state and observer state are all in memory,
so none of them survives a restart. The browser keeps the same session ID and counters across one, so the
validated counters are the usable evidence: only a crossing a deck observes counts. The first valid
observation (fresh, this session, active or paused) sets `counter_baseline`, and any counter milestone
already met is recorded as `skipped: reached_before_first_observation`. The baseline is taken on every
poll, even while speech is blocked.

- **A milestone crossed during downtime is not announced.** The failure is silence, never a repeat.
- **A milestone reached but not yet delivered** when the service stops is also lost.
- **A model switch mid-session behaves the same way:** the new model starts from the current counters.
- **The opening can still repeat** if a restart happens within `opening_window_seconds` (120 s).
- **Event-triggered sequences** dedupe in memory only. No shipped card uses them.

## Priority

Session end > session start > mission > narrative > normal. Only normal cards wait for the
countdown. Safety notices do not pass through the deck.

`arrival` is a registered lane, but its cards play outside any session's deck, through one `Arrival` per model
activation. It has no place in this order and is not in this table: a pending closing, reaction or session holds it
back, and it never enters the shuffle. See "Arrival lifecycle" below.

| Lane | Countdown | Unsolicited limit | 30 s conversation hold |
|---|---|---|---|
| Session start | Bypassed | Bypassed | Bypassed |
| Session end | Bypassed | Bypassed | Bypassed |
| Mission | Bypassed; 4 s between missions | Bypassed; doesn't count | Bypassed |
| Narrative | Bypassed | Counts; applies only when the cap is on | Applies |
| Normal | Applies | Counts; applies only when the cap is on | Applies |

Every lane waits for free output and is blocked by quiet mode, user activity and protective states.

## Timing

**Countdown (`countdown_seconds`, default 10).** It runs from the *estimated* end of the last
response of any kind. That estimate is `busy_until`: words / 2.5 seconds, between 2 and 30. Actual
speech playback is not measured, so a next card can be early or late relative to real audio. Cards
are polled every 250 ms, so a normal card starts 10 to 10.25 seconds after the estimated end.

**Recent-conversation hold (`user_idle_before_spontaneous_seconds`, default 30).** This is the
Director's existing per-model setting, not a deck setting. It holds narrative and normal cards until
30 seconds after the user's last real message. Unsolicited turns never move it, so without user
messages it never affects cadence.

It runs *alongside* the countdown rather than being added to it. After a user message, the next normal
card comes at whichever is later:

- 30 seconds after the user's message
- 10 seconds after the estimated end of the reply

A user who keeps replying within 30 seconds therefore gets no normal cards, which is intended: the
conversation is already active. Setting the value to 0 removes the hold.

**Unsolicited limit (`unlimited_unsolicited`, default on; `max_consecutive_unsolicited`, 1–50,
default 50).** By default there is no cap: cards keep coming for as long as the other gates allow.
With **Unlimited unsolicited replies** switched off, normal and narrative cards count toward the cap
and only a user message resets it. At roughly 15 seconds per card, an uninterrupted session reaches a
cap of 50 after about 12 minutes, and normal cards then stop until the user speaks. The count is kept
either way and shows in diagnostics. Saved settings without the field load as unlimited; a saved cap
is kept for when the toggle is switched off.

## Closing

The first finalized session result wins. Later completion signals change nothing, and the card uses
only that stored result, even after counters reset.

- **Commentary is superseded at once:** queued cards and reactions are discarded, a generating
  unsolicited turn is cancelled, and commentary still playing gets `speech_cancel`.
- **Never cancelled:** a user's reply. A safety notice just issued gets a 2-second hold instead.
- **Waiting doesn't lose the closing:** output or user activity holds it without spending
  `closing_ttl_seconds`. Only `closing_max_hold_seconds` (default 300) limits that wait, including when
  polling stops during a long user turn.
- **Deliberate blocks spend the TTL (default 60 s):** safety, mute, quiet and disconnect. The closing
  is then dropped rather than delivered out of context. Nothing forces it through any of these.
- **It is not offered `[SILENCE]`,** unlike every optional card. A model can still emit it, and that counts as
  an unproductive attempt.
- **Bounded retries:** a silent, rejected or failed attempt costs one of `max_attempts` (default 2), with
  `interruption_retry_seconds` between them. An interruption costs one of `max_interruptions` (default 3), and a user
  turn still takes precedence. The hold limit and TTL go on applying throughout.
- **Repetition:** the usual regeneration applies, but repeated wording alone can't lose the closing. If it still
  repeats, it is delivered and the Director logs `closing_repetition_kept`.
- **A spent retry on a factual error:** a rejected draft is corrected without inference (see "Checks on these cards"),
  and the check runs again on the corrected text. If nothing passes, the attempt counts as suppressed.
- **A dropped closing is never silent:** whichever way a pending closing ends, the deck tells the service at that
  point. Anything but delivery logs `deck_closing_dropped` and publishes `ai_diagnostics` with `closing_outcome`, which
  the deck snapshot also keeps.

| `closing_outcome` | Meaning |
|---|---|
| `delivered` | Published; not a drop |
| `expired` | A deliberate block outlasted `closing_ttl_seconds` |
| `hold_limit_reached` | Waiting outlasted `closing_max_hold_seconds` |
| `suppressed`, `failed` | Attempts exhausted, by silence or rejection, or by inference failure |
| `interruptions_exhausted` | Cancelled `max_interruptions` times |
| `superseded` | The service moved to another session's or model's deck, or the deck was turned off |
| `service_closed` | The service stopped first |

`closing_rejected` is separate: a closing that was never permitted, such as after a safety stop, is not a drop.

## History on Arrival and Closing cards (Phase 1E)

The Director supplies the occasion and verified facts; the companion's personality supplies the reaction.
No character tone is classified or scripted. If the participant has set an active story objective, the
prompt lets it decide the attitude, and it changes no fact, limit or permission. Modelfiles are untouched.

`companion_ai/session_history.py` is read-only and returns one bounded projection: edges, active running
seconds, experience, goal, outcome and whether the record is comparable. Session IDs, companion lists, heart
rates and settings never reach the model.

| Lookup state | Meaning | Arrival card |
|---|---|---|
| `found` | A record that belongs to this exact model scope alone, including the session an idle observer still names | `arrival-returning` |
| `none` | AI access on, recording on, and nothing suggests a gap | `arrival-first`, which is told this is a first session and says so in its own words |
| `denied` | AI access off, even if records exist | `arrival-greeting` |
| `unavailable` | No Journal, or it could not be read | `arrival-greeting` |
| `incomplete` | Recording off, Journal full, deleted records, a shared or unattributed row, a sibling model's record, or a session known by other means that the Journal doesn't hold | `arrival-greeting` |

**Model scope.** Only rows whose companions are all this exact scope are read, for every companion, which is
stricter than `SessionJournal.retrieve`. A shared row is unread by all of its companions. Scope includes the
endpoint and model version, so a new version of a model has no readable history. Its predecessor's records
only make the lookup `incomplete`, so that it can't claim a first session.

**Which session is read.** While IDLE the observer keeps the ID of the most recently completed session, so that ID
says nothing about what may be read, and `session_history` excludes only what its caller names. An Arrival names
nothing and gets the latest eligible session and its true interval.

**Closing comparison.** The previous session is looked up with the finalized session's ID explicitly excluded, so a record
the Journal has just persisted can't be compared with itself. Directions and differences are computed in code
from the finalized result and carry no verdict. A checkpoint-only or partial earlier record gives no comparison.

**Arrival lifecycle.** One `Arrival` per change of model scope, outside any session's deck, so the shuffle doesn't
shift and the definition revision stays 2.

- **Duplicates:** refreshes and repeated state updates don't change the scope, so they can't re-arm it. Only one
  generation is attempted. Returning to a companion within `arrival_repeat_seconds` (default 300) isn't an arrival.
- **Rapid switching:** nothing generates until `arrival_settle_seconds` (default 3) have passed on one companion.
- **Cancelled by:** a session starting, a user turn, or a model change, including during generation.
- **Waits for, up to `arrival_ttl_seconds` (default 120):** mute, quiet, stale observation, protective state, user
  activity, output and pending reactions. The clock starts at the first poll after activation, and that poll needs
  a current observer report but no hardware. Expiry cancels it with reason `expired`.
- **The time limit covers only the wait.** Once generating, it is bounded by the model timeout instead.
- **Rechecked before publishing:** the live and adapter model scope, a running backend, status, the deck and Director
  settings, proactive speech, mute, quiet, observation freshness, emergency and protective state, and any user turn
  since it was armed. If any of these has changed, it is cancelled, logged as `arrival_cancelled: stale_at_delivery`,
  and `response_suppressed` is published. It is not retried.
- **Needs no hardware or session in progress.** It isn't counted as unsolicited commentary and writes no Story Memory.

**Checks on these cards.** `history_violations` in `fidelity.py` refuses, with one correction and then suppression:
figures that weren't dealt (in any clause), a comparison that contradicts the computed one, a wrong final edge, a
wrong time since, a first-session or shared-past claim the lookup doesn't support, a statement of health or fitness
as fact, an objective standard, and a figure credited to the wrong session. A Closing whose retry is spent drops
the sentences that failed and states the recorded figures plainly, so the card still arrives without the error and
without another inference. Every deck card, on every lane, also refuses a companion calling the person by the
companion's own name. On these cards the dealt facts replace other history as
grounding, so in-memory sessions can't stand in for Journal permission. These are pattern checks, not a language
verifier, and unusual wording can pass.

**Dialogue tone is never a reason to refuse a line.** No check rejects a line for being demanding, provocative or
dominant, on any lane, and no card brief or card instruction asks a character to hold back on those grounds. The
one baseline sentence in `GROUNDING` shared with non-card turns is unchanged. Generated dialogue still has no authority over the device: it can't change settings or
override a safeguard, and a line claiming to have done so is refused as a false control claim. Hardware protections,
emergency stops, user controls, mute and session lifecycle rules are deterministic and don't read dialogue.

**What these checks deliberately allow** (see the suppression audit). Teasing about stamina or endurance, asking
what someone felt, demands and challenges of any intensity, an uncertain reading such as "either your stamina is
growing or you refuse to yield", opinions about what already happened, and a character's own stories about time or
numbers are the character's voice. A duration is checked only when it is said of a session or the person's performance
in one, so "I spent two hours in the greenhouse this week" and "give me five minutes" stay free. Time said to have
been spent together counts as that, in words or digits: "You spent ninety minutes with me" is checked against the
verified time, while "We spent two hours together in the ruins", "You spent two hours with me yesterday" and "She
spent ninety minutes with me" aren't. A comparison is read clause by clause, and only counts when it refers to the session's own length or edges: "savor the afterglow a little
longer" and "longer than I expected" claim nothing about the earlier session, and "the last one" isn't the number one.

**Which session a comparison describes.** What follows "than" is the yardstick, so "more edges than last time" is said of
this session and "longer last time than this" of the earlier one. Otherwise the session named nearest is the subject,
at either end: "you had more edges last time" and "last time you lasted longer" both describe the earlier session, and
so claim the opposite direction for this one. A negation rules out one direction only. The computed comparison decides.
Each comparative in a sentence is its own claim, with its own direction, count and negation: in "This session ran longer
than the last one and had fewer edges", both parts are checked, and "had fewer edges" keeps the subject of the part
before it. A part whose "you" could mean either session claims nothing.

Limits: a bare "you lasted longer", with no session named, isn't read as a comparison. A figure with no anchor in its
own sentence ("Your last session. It was long, thirteen minutes of it, somehow.") can pass.

## Event commentary while the deck is on

The deck owns unsolicited commentary, so one occurrence can't get both a reaction and a card. Events
still go through detection, Event Intelligence, the occurrence ledger and recent context, and are
recorded as `context_only:deck_owned`. Verified events with an ID can trigger cards.

The one retained reaction outside the deck acknowledges the user's own selection (`experience_changed`,
`goal_changed`), unless a card subscribes to that event. Safety notices are unaffected.

## Faults

If an enabled deck cannot run, because of an internal error, an invalid definition or an invalid
settings file, that model gets **no unsolicited dialogue**. Legacy initiative is deliberately not a
fallback, because it lacks the deck's protective-state gates.

- Queued reactions are discarded and a generating unsolicited turn is cancelled.
- User conversation and safety notices continue.
- `character_state` reports `event_deck_fault` with the error, `ai_diagnostics` carries it once, and
  the Director's decision reads `deck_fault`. There is no dedicated UI for this yet.
- A runtime fault lasts until restart. A corrected settings file is read when the model is next
  activated or at restart.

## Benchmark

```sh
PYTHONPATH=. .venv/bin/python -m tests.fork.deck_session_benchmark --output /tmp/deck-session.json
```

It uses the real scheduler, deck and compiler at the production poll rate with mocked Ollama.
`tests/fork/test_deck_session_benchmark.py` asserts its invariants. It does not measure prose quality,
live latency or audio playback.

## Known test issues, unrelated to the deck

- The three former baseline failures in `test_context_only_or_disabled_never_generates` pass now that idle
  initiative is retired.
- The intermittent `'119'` UUID flaw in `test_event_turn_receives_completed_user_history_and_no_numerical_prompt`
  is gone: that test now checks that a telemetry event without the deck is recorded but never spoken.
