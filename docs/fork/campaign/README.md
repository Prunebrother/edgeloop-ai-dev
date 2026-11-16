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

The campaign runs inside the observer. It reads the same accepted engine evidence as the Session Journal, the canonical report built after `BrowserObservation.accept`. It never reads chat or model output. The browser can only ask for three things (`campaign` message: `get`, `start`, `abandon`). The observer checks each request and answers with `campaign_state` or, when a mission is done, a single `mission_result`.

## Files

- `config/campaigns/<id>/campaign.json` holds the rules: missions, prerequisites, objectives, rewards, the session mode, the AI settings limit and replay. It is validated by `Campaign` in `campaign.py`. Unknown fields, unknown prerequisites, cycles and companions that are never unlocked are all rejected. A broken campaign is skipped and the others still load.
- `config/campaigns/<id>/narrative.json` holds the scripted character lines: a briefing and a completion line per mission, an optional `milestones` reaction per objective, and optional `director_context`. `status` is `draft` until the author approves the text.
- To add a campaign, add a folder. The menu lists campaigns by `order`.

## Objective types and their evidence

| Type | Met when (all from the engine's own report) |
|---|---|
| `hr_monitor_connected` | `devices.hr_ready` and `devices.ble`, and **not** `simulated_hr`. The built-in simulator never counts. |
| `toy_connected` | `devices.toy_ready` |
| `session_started` | The status is RUNNING with the mission's companion selected, a real heart-rate monitor and a toy, in the required `session.active_mode` if the mission sets one. This session becomes the **mission session**. |
| `edge_count` | The engine's edge counter rose by `count` during the mission session while the mission companion was selected. |
| `orgasm_count` | Orgasms the participant reported during the mission session: `orgasm_count` rising (I came, Calibration's Finished me), or Survival's Finished me (`completion_reported`), or Came Early. Each report counts once. |
| `calibration_completed` | The Calibration run ended: `terminal_outcome == calibration_completed` or the accepted `completion_accepted` event. |
| `calibration_saved` | On that ending, `details.calibration_saved` is true. This is the engine's own result of writing the saved maximum to its settings store. The value is kept in the campaign record. |

Counts restart when the mission session ends before the mission is done; that decision is recorded below. A mission completes the moment its last objective is met. The running session is never stopped, and the player can keep playing.

## Rewards

| Type | Effect today |
|---|---|
| `unlock_companion` | The companion becomes available **for this campaign**. The Freeplay roster is never limited. |
| `milestone`, `campaign_complete` | Recorded. `campaign_complete` also marks the campaign completed. |
| `story_branch`, `collectible`, `achievement` | Recorded as earned only. A later feature can act on them. |

Rewards are stored by key (`type:id`), so a replay or a retried save never grants anything twice. A successor mission unlocks through its `prerequisites`, which are the single source of truth for unlocks. A mission with a companion also needs that companion to be unlocked.

## Saved progress

`campaign-progress.json` sits in the observer data directory, next to the Session Journal:

```json
{"schema_version": 1,
 "campaigns": {"asterion_initiative": {
    "missions": {"orientation": {"completions": 1, "first_completed_at": "…", "last_completed_at": "…"}},
    "rewards": {"unlock_companion:evelyn": {"earned_at": "…", "mission": "orientation"}},
    "completed_at": null, "records": {}}},
 "active": {"campaign": "asterion_initiative", "mission": "first_assessment", "started_at": "…"}}
```

- **Save first, announce after:** completion is written to disk before anything is announced. If the write fails, nothing is announced, a notice is shown, and the save is retried on the next update.
- **Missing or bad file:** a missing file starts fresh. An unreadable, invalid or newer-version file is **left untouched**, and only the campaign is switched off. Freeplay is unaffected.
- **Removed content:** progress for a removed campaign or mission is ignored.
- **Not resumed:** the active mission is resumed after a restart, but a session never is, so counts start again.
- **Migration:** add a function `MIGRATIONS[n]` that turns version *n* into *n+1* and raise `SCHEMA_VERSION`. Files from a newer app are never rewritten.

## The Asterion Initiative (decisions of 2026-11-16)

| # | Mission | Companion | Completion | Reward |
|---|---|---|---|---|
| 1 | Orientation | Nova | 1 edge | Evelyn + Mission 2 |
| 2 | First Assessment | Evelyn | 5 edges in one session | Daisy + Mission 3 |
| 3 | Country Connections | Daisy | 1 reported orgasm | Celeste + Mission 4 |
| 4 | The Director's Test | Celeste | 5 edges + 1 orgasm in one session | Mission 5 |
| 5 | Asterion Certification | Nova | Calibration run ended with **Finished me** and the max saved | Campaign complete |

Every mission also needs a real heart-rate monitor, a toy and a session started with that companion. Decisions:

- Mission 5 uses **Calibration** mode. Edge Training saves no baseline.
- Only Finished me certifies, because it both saves the max and counts the orgasm. Edged saves the max but ends the run without an orgasm, so the mission explains this and stays open.
- The heart-rate **simulator does not count**.
- Counts **restart per session**.
- Mission 5 limits AI Settings Control to **intensity**; the model is told so and other requests are dropped. Pause and stop by the player, the Emergency stop and all engine safety stay as they are.
- Mira is not in this campaign.

**Placeholders pending narrative design:** all briefing and completion text in `narrative.json` is a draft written from the existing lore (`characters/lore/*`), not approved dialogue. The objective rules above are the approved design.

## Screens

- **Main menu:** shown after the age gate and the setup wizard.
- **Campaign selection, then mission selection:** missions are marked completed, active, available or locked, with the reason and the rewards.
- **Briefing:** the scripted lines, the objectives and the hints. "Begin" selects the mission's companion and shows the briefing in the conversation.
- **Mission banner** above the conversation: live objective ticks, plus notes when the wrong companion is selected or the session ended early.
- **Completion:** a small notice in the banner, with the completion line in the conversation. **Results** opens once the session is stopped.
- The **Menu** button in the dashboard bar is disabled while a session runs, pauses or ramps down. The menu closes itself if a session starts some other way, such as a gamepad. Choosing Freeplay leaves a mission in progress after a confirmation; completed missions are kept.
- Keyboard: arrow keys move between tiles and skip the disabled one, Escape goes back, Tab stays inside the menu, and engine shortcuts such as Space do not reach the session while the menu is open.

## Known limits and missing integration points

- **Orgasm** evidence is always the participant's own report through an EdgeLoop control. There is no sensor detection.
- **Scripted lines** are shown in the conversation but not sent to the model, so the companion does not know about the mission yet. `director_context` and `milestones` are where short mission context goes once the dialogue is written and tested.
- **Story milestones and registered challenges** have no authoritative event yet, so they are not objective types.
- **Freeplay unlocks:** campaign companion unlocks do not change Freeplay. A future reward option such as `grants_freeplay` can add that.
- **Size:** the campaign view is about 9 KB. Keep a campaign well under the 64 KB message limit, or load briefings on demand.

## Tests

- `tests/ai/test_campaign.py`: definitions, prerequisites, every objective type, rewards, replay, persistence, bad files, isolation, the settings limit, and a mission played through the real observer WebSocket.
- `tests/fork/campaign-browser.mjs`: menu, keyboard, Freeplay with the Character Builder, campaign and mission screens, briefing, completion, results, reload, leaving a mission, the menu lock during a running session, and phone width. Mission evidence comes from a test-only fixture endpoint, because a browser test cannot connect a real strap and toy.
