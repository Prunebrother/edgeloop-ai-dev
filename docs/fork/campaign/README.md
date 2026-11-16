# Campaign mode

EdgeLoop AI opens on a main menu with three choices:

- **Campaign:** story missions.
- **Freeplay:** the app as it was before the menu existed, with every companion, Mira and the Character Builder.
- **Companion Builder:** a disabled tile marked "Coming soon". It stands for a future feature and has nothing to do with the existing Character Builder.

## Who does what

| Part | Owns |
|---|---|
| Character model (Modelfile) | Personality and dialogue. Not changed by the campaign. |
| Character Cards / event deck | Situational variation. Not changed. |
| Director | When the companion speaks. Not changed. |
| **Campaign** (`companion_ai/campaign.py`) | Missions, objective checks, progress, rewards. |
| Main menu (`src/js/ai/main-menu.js`) | Screens only. It never decides progress. |

The campaign runs inside the observer. It reads the same accepted engine evidence as the Session Journal, the canonical report built after `BrowserObservation.accept`. It never reads chat or model output. The browser can only ask for three things (`campaign` message: `get`, `start`, `abandon`). The observer checks each request and answers with `campaign_state` or, when a mission is done, a single `mission_result`. While a mission runs it also sends `campaign_progress` (only the try's counts and stage clocks, about 1.5 KB, since stage clocks change every second) and `mission_milestone` (a scripted progress line, once per try).

## Files

- `config/campaigns/<id>/campaign.json` holds the rules: chapters, missions, prerequisites, objectives, rewards, the session mode, the AI settings limit, replay and `review` (earlier missions whose saved results the companion is told about). A mission belongs to the chapter named by `story.chapter`; a chapter is complete when its `chapter_complete` reward is earned. It is validated by `Campaign` in `campaign.py`. Unknown fields, unknown prerequisites, cycles and companions that are never unlocked are all rejected. A broken campaign is skipped and the others still load.
- `config/campaigns/<id>/narrative.json` holds the scripted character lines: a briefing and a completion line per mission, `milestones`, optional `director_context`, and a closing block per chapter (`chapters`). `status` is `draft` until the author approves the text; a single block can also carry `"status": "draft"` inside an approved narrative, and the menu marks such missions "Story draft".
- Milestone keys: `start` (the mission session begins), `<objective>:<n>` (a count threshold from `milestones`, or the n-th completed play-style stage), `<objective>:<stage id>` (that stage of a sequence begins) and `<objective>:done` (a goal is met while the mission is still open). A goal with a scripted `:done` line gets no model card for that moment, so it is never marked twice.
- To add a campaign, add a folder. The menu lists campaigns by `order`.

## Objective types and their evidence

| Type | Met when (all from the engine's own report) |
|---|---|
| `hr_monitor_connected` | `devices.hr_ready` and `devices.ble`, and **not** `simulated_hr`. The built-in simulator never counts. |
| `toy_connected` | `devices.toy_ready` |
| `session_started` | The status is RUNNING with the mission's companion selected, a real heart-rate monitor and a toy, in the required `session.active_mode` if the mission sets one. This session becomes the **mission session**. |
| `edge_count` | The engine's edge counter rose by `count` during the mission session while every mission condition held: the mission companion selected, a real heart-rate monitor (not the simulator), a toy and the mission's mode. Activity without them only moves the baselines on, so it never counts later. |
| `orgasm_count` | Orgasms the participant reported during the mission session, under the same conditions: each rise of the engine's `orgasm_count` (I came; Finished me in Survival and Calibration once confirmed) and each accepted Came Early (which ends the session without raising the counter) counts separately. `completion_reported` is never evidence: Finished me sets it before its confirm, so a cancelled Finished me leaves it set (in Calibration, then Edged would end the run with no orgasm). |
| `calibration_completed` | The Calibration run ended: `terminal_outcome == calibration_completed` or the accepted `completion_accepted` event. |
| `calibration_saved` | On that ending, `details.calibration_saved` is true. This is the engine's own result of writing the saved maximum to its settings store. The value is kept in the campaign record. |
| `style_stages` | `count` different play styles (snapshot `experience`), each run for `seconds` of active time with no game on (`goal == 'tease'`). A style fills at most one stage and keeps its time when the player switches away and back. |
| `stage_sequence` | `stages` in order, each `seconds` of active time at its `intensity` (snapshot %, within `tolerance`). Time at another intensity does not count; the stage clock waits. |

Options on counted objectives: `milestones` (thresholds below `count` that get a scripted line) and `after` (count only events that come once that earlier objective is met: Mission 9's finish counts only after the assessment).

**Active time** is the engine's own running clock (`seconds`, which only advances while RUNNING). An interval between two observations is credited only when both ends were RUNNING, met every mission condition and had the same configuration (play style and game, or intensity), and it is at most 5 seconds long. So a pause, a setting change, the simulator or a reconnect gap counts for nothing, and the same configuration can never fill two stages. Observations arrive about once a second.

Counts restart when the mission session ends before the mission is done; that decision is recorded below. A mission completes the moment its last objective is met. The running session is never stopped, and the player can keep playing.

## What the companion knows

Only the mission's own companion is told about it, and only the campaign's verified state is used. A custom character is its own persona (`custom:<identity>`), even on a built-in companion's model: it never plays, advances or hears about that companion's missions, and "Begin" switches to the built-in companion. The companion can never complete, end or pause anything for the mission.

- **Mission brief** (`CampaignService.model_context`): a few factual lines added to every chat reply and Director card for that companion. They cover the mission and its goal, verified progress in this session (for example "2 of 5 edges"), and what the participant needs to do to begin. After completion the brief says the mission is complete and saved, until the next session starts. Cards are told to mention it only if it fits; chat replies are told to answer from it when asked what to do or how it's going.
- **Mission moments** (`campaign_moment` cards): the companion reacts in its own words when the mission is completed and saved, or when one goal is reached while another remains (Celeste: the 5 edges or the orgasm, whichever comes first). Setup steps (strap, toy, session start) are not moments. In Calibration, Finished me reports the orgasm and ends the run a moment later, so that is one completion card. The cards play after the Director's own reaction (an orgasm or edge card comes first). The same rule is checked before a card starts and again before it is delivered. It holds the card during a watchdog pause, no-contact, signal loss, a stale observation, a quiet request, spontaneous commentary off or speech disabled. It drops the card when the campaign says the moment is no longer true (`CampaignService.cue_valid`): a goal belongs to one try, so a reset, an abandon or completion makes it stale. Cards are also dropped after 120 seconds or when the companion changes. After the session ends, only a completion may play (Calibration's Finished me, Came Early), and never after an Emergency stop (`terminal_outcome: safety_stop`). A safety event drops queued goal cards. An Emergency stop drops them all and silences that session for good, so a completion found in the same observation never speaks either. The progress itself still counts.
- **Fresh at dispatch:** the brief is rebuilt when the reply is actually generated and at each validation step, so a reply queued at "2 of 5" never goes out with stale progress.
- **Target numbers:** the card checker accepts a mission target only in a target phrase that claims no achievement ("of the five edges", "out of five edges", "the five edges I asked for"). "Five edges for my assessment" and "you have reached the five edges I asked for" are counts, and must match the engine's edge counter.
- **Open missions:** a reply that says the open mission is complete or passed is corrected. The check works clause by clause, so "The mission is complete, but we are not stopping" is caught. A claim about another mission (its title, "Mission 2", its companion, or "earlier test") is not, but only that claim is excused: "you passed my test just as you passed Evelyn's" is still caught.
- **Not sent:** the scripted briefing and completion text. The brief says the participant has read the briefing and that the completion message is on screen, so the companion doesn't repeat them.
- **Live check:** `tools/campaign_live_check.py` plays every mission against the real local models, with no browser or hardware, and records each line with the card that produced it.

## Rewards

| Type | Effect today |
|---|---|
| `unlock_companion` | The companion becomes available **for this campaign**. The Freeplay roster is never limited. |
| `milestone`, `chapter_complete`, `campaign_complete` | Recorded. `chapter_complete` marks its chapter completed, `campaign_complete` the campaign. |
| `story_branch`, `collectible`, `achievement` | Recorded as earned only. A later feature can act on them. |

Rewards are stored by key (`type:id`), so a replay or a retried save never grants anything twice. A successor mission unlocks through its `prerequisites`, which are the single source of truth for unlocks. A mission with a companion also needs that companion to be unlocked.

## Saved progress

`campaign-progress.json` sits in the observer data directory, next to the Session Journal:

```json
{"schema_version": 2,
 "campaigns": {"asterion_initiative": {
    "missions": {"orientation": {"completions": 1, "first_completed_at": "…", "last_completed_at": "…"}},
    "rewards": {"unlock_companion:evelyn": {"earned_at": "…", "mission": "orientation"}},
    "chapters": {"introduction": {"completed_at": "…"}},
    "completed_at": null, "records": {"orientation.edge": 1}}},
 "active": {"campaign": "asterion_initiative", "mission": "first_assessment", "started_at": "…"}}
```

- **Save first, announce after:** completion is written to disk before anything is announced. If the write fails, nothing is announced, a notice is shown, and the completion is kept as pending. It is saved on the next update, before anything else, so a new session cannot discard it.
- **Missing or bad file:** only a missing file starts fresh. An unreadable, invalid, `null` or newer-version file is **left untouched**, and only the campaign is switched off. Freeplay is unaffected.
- **Removed content:** progress for a removed campaign or mission is ignored.
- **Not resumed:** the active mission is resumed after a restart, but a session never is, so counts start again.
- **Migration:** add a function `MIGRATIONS[n]` that turns version *n* into *n+1* and raise `SCHEMA_VERSION`. Files from a newer app are never rewritten.
- **Version 1 to 2 (Chapter 2):** adds `chapters`. Completion markers (`completed_at`, `chapter_complete`/`campaign_complete` rewards) are dropped and recomputed on load from the completed missions under the current definitions, with each mission's first completion time. A player who finished the old five-mission campaign therefore has Chapter 1 complete, Mission 6 available and the campaign open again; every mission, completion count, record and other reward is kept. The file is written as version 2 on the next save. An older app then refuses the file (newer version) and switches only its campaign off.
- **Records:** each completion keeps its verified results as `<mission>.<objective>` (counts reached, play styles used). Missions completed before this existed have none, so a later review says "completed, with no further detail on record".

## The Asterion Initiative (decisions of 2026-11-16)

**Chapter 1: Introduction**

| # | Mission | Companion | Completion | Reward |
|---|---|---|---|---|
| 1 | Orientation | Nova | 1 edge | Evelyn + Mission 2 |
| 2 | First Assessment | Evelyn | 5 edges in one session | Daisy + Mission 3 |
| 3 | Country Connections | Daisy | 1 reported orgasm | Celeste + Mission 4 |
| 4 | The Director's Test | Celeste | 5 edges + 1 orgasm in one session | Mission 5 |
| 5 | Asterion Certification | Nova | Calibration run ended with **Finished me** and the max saved | Chapter 1 complete + Mission 6 |

**Chapter 2: Advanced Research** (narrative is a DRAFT awaiting review)

| # | Mission | Companion | Completion | Reward |
|---|---|---|---|---|
| 6 | The Endurance Study | Evelyn | 15 edges in one session; lines at 5 and 10 | Mission 7 |
| 7 | The Cloverfield Quota | Daisy | 2 reported orgasms in one session (pausing allowed); line at the first | Mission 8 |
| 8 | Adaptive Systems Calibration | Nova | 4 different play styles, 5 minutes of active time each, no game on, one session | Mission 9 |
| 9 | The Director's Reassessment | Celeste | 30 minutes of active time in 3 stages at **75%, 100%, 125%** intensity (set by the player), **then** a reported orgasm | Chapter 2 + campaign complete |

Chapter 2 decisions (2026-11-16):

- Mission 8: any four of the eight play styles, chosen by the player; a game switched on stops the clock.
- Mission 9: the intensity per stage is fixed. The player sets it (Celeste asks; with AI Settings Control allowed she may set it herself, and in the final phase she may also switch Force Orgasm). Time at another intensity just waits, nothing is lost; there is no alternative path. The mission completes only after the finish (a reported orgasm after the assessment). The player can pause, stop or use the Emergency stop at any time.
- Celeste is told the saved results of Missions 6 to 8 (`review`), and only those.

Every mission also needs a real heart-rate monitor, a toy and a session started with that companion. Decisions:

- Mission 5 uses **Calibration** mode. Edge Training saves no baseline.
- Only Finished me certifies, because it both saves the max and counts the orgasm. Edged saves the max but ends the run without an orgasm, so the mission explains this and stays open.
- The heart-rate **simulator does not count**.
- Counts **restart per session**.
- Mission 5 limits AI Settings Control to **intensity**; the model is told so and other requests are dropped. Pause and stop by the player, the Emergency stop and all engine safety stay as they are.
- Mira is not in this campaign.

**Narrative:** `narrative.json` is Narrative V2, written and approved by the author on 2026-11-16 (status `approved`). It adds one canon fact to `characters/lore/core_canon.md`: only 1% of men worldwide remain fertile (IRRA estimate). The character models do not know that figure until a later model update. Daisy's remark on quality and volume after Mission 3 is deliberate flavour, not a measurement. Its campaign closing lines (Nova, after Mission 5) are now Chapter 1's closing block (`chapters.introduction`), unchanged. Chapter 2's lines (Missions 6 to 9, their milestones and the chapter close) are DRAFT text marked per block.

## Screens

- **Main menu:** shown after the age gate and the setup wizard.
- **Campaign selection, then mission selection:** each chapter shows its title, completion percentage or "Locked". Missions are grouped under their chapter and marked completed, active, available or locked, with the reason, prerequisites, objectives (with milestones and stages) and the rewards.
- **Briefing:** the scripted lines, the objectives and the hints. "Begin" selects the mission's companion and shows the briefing in the conversation.
- **Mission banner** above the conversation: live objective ticks and counts, milestone ticks, the play-style stages (current one, time per stage, time to go, overall %) or the stage sequence (current stage, its intensity and clock, total and %), plus notes when the wrong companion is selected or the session ended early. Scripted milestone lines appear in the conversation as "Mission update".
- **Chapter completion:** the results screen and the conversation show the chapter's closing lines after the mission's own.
- **Completion:** a small notice in the banner, with the completion line in the conversation. **Results** opens once the session is stopped.
- The **Menu** button in the dashboard bar is disabled while a session runs, pauses or ramps down. The menu closes itself if a session starts some other way, such as a gamepad. Choosing Freeplay leaves a mission in progress after a confirmation; completed missions are kept.
- Keyboard: arrow keys move between tiles and skip the disabled one, Escape goes back, and Tab stays inside the menu. While the menu is open (and the age gate or setup wizard isn't above it), a window-level guard stops every key from outside the menu before the engine's shortcuts see it, and moves focus back into the menu.
- Freeplay during a mission waits for the observer to confirm the mission was left. If the save fails or the service is unreachable, the menu stays open and says so.
- Mission lines queued during a companion switch belong to that switch. They are dropped if it fails, the service disconnects, or another model or a custom character is selected.

## Known limits and missing integration points

- **Orgasm** evidence is always the participant's own report through an EdgeLoop control. There is no sensor detection.
- **Scripted lines** are shown in the conversation but not sent to the model, which only gets the factual brief. `director_context` (an optional author line added to the brief) and `milestones` (scripted reactions per goal) are unused in the Asterion Initiative.
- **Story milestones and registered challenges** have no authoritative event yet, so they are not objective types. Optional challenge objectives and alternative completion paths are not implemented: no Chapter 2 mission uses them (Mission 9's alternative path was declined).
- **Per session:** Chapter 2 progress, like Chapter 1, restarts when the session ends. Mission 8 and 9 each need about 20 and 30 minutes in one session.
- **Campaign completion:** the campaign completes with Mission 9. A later chapter needs another migration that reopens it, as version 2 did.
- **Freeplay unlocks:** campaign companion unlocks do not change Freeplay. A future reward option such as `grants_freeplay` can add that.
- **Size:** the campaign view is about 9 KB. Keep a campaign well under the 64 KB message limit, or load briefings on demand.

## Tests

- `tests/ai/test_campaign.py`: definitions, prerequisites, every objective type, rewards, replay, persistence, bad files, isolation, the settings limit, and a mission played through the real observer WebSocket.
- `tests/ai/test_campaign_chapter2.py`: chapters and unlocking, companion restrictions, milestones, the two-report quota, play-style time (pauses, games, style changes, gaps, the simulator), the staged assessment and its finish, stopping in any stage, the review brief, replay, the version 1 migration, malformed and removed records.
- `tests/fork/campaign-browser.mjs`: menu, keyboard, Freeplay with the Character Builder, campaign and mission screens, briefing, completion, results, reload, leaving a mission, the menu lock during a running session, and phone width. Mission evidence comes from a test-only fixture endpoint, because a browser test cannot connect a real strap and toy.
