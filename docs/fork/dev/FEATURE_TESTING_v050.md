# v0.5.0 development build: supervised feature testing

Status, 2026-11-05: `experiment/ai-companion` includes the Character Card merge `55c9fd8` and the Player workspace (fast-forwarded to `feature/player-workspace`; checkpoint tag `checkpoint/pre-player-workspace-merge-20261105` → `a3cb88e`). Local only: not pushed, released or exported. This guide covers simulator-only testing first and lists what must be true before any supervised hardware session.

## What the build contains

- Upstream EdgeLoop 1.1.4.x (`upstream/main` `d3c5df3`; engine version 1.1.4.33), merged in `cfbf00d`.
- 48 Character Cards (12 each for Nova, Daisy, Evelyn and Celeste) and the 19 Common Cards.
  - `config/event-deck.json` is byte-identical to the personal checkpoint `75d38d8`: SHA-256 `39e04b7c…95c1cb`.
- Card-history separation (`b4bb068`): earlier conversation reaches a card prompt as an assistant-side background message, not inside the current instruction.
- The video player with funscript follow, Theater and Fullscreen.
  - The player opens only from the **Player** button and closes with **✕ Close player**. When open, it sits above a compact chat in the centre column. Closing it keeps playback, the session and the conversation.
  - Theater covers all three columns. In Theater and Fullscreen an **Emergency stop** sits inside the video.
  - Loading a video + funscript switches to Script without a Director comment. Your own play style and endgame choices are still acknowledged.
- Bratty Tease and Script play styles, visible to the companion. Pause reasons reach the companion.
- No Agent Link (see `AGENT_LINK_BOUNDARY.md`). The AI side has no command path.

## Where and how to run it

Working directory: `~/projects/edgeloop-ai-fork`. Check that you're on `experiment/ai-companion` with `git status`.

Services, all loopback-only:

| Service | Port | systemd user unit |
|---|---|---|
| Dedicated Ollama | `127.0.0.1:11435` (models in `~/.ollama/models`) | `edgeloop-ai-ollama.service` |
| AI observer (read-only) | `127.0.0.1:8768` | `edgeloop-ai-observer.service` |
| EdgeLoop web page | `http://127.0.0.1:8770/` | `edgeloop-ai-web.service` |

The units run straight from this checkout, so the desktop launcher always serves the code currently checked out here.

```bash
cd ~/projects/edgeloop-ai-fork
tools/launch-desktop.sh start              # start the services and open the browser (same as the "EdgeLoop AI" menu entry / ~/.local/bin/edgeloop-ai start)
tools/launch-desktop.sh start --no-browser # services only; open http://127.0.0.1:8770/ yourself
tools/launch-desktop.sh status
tools/launch-desktop.sh stop               # stops web, observer and the dedicated Ollama
```

The page pairs with the observer automatically (desktop pairing, through `$XDG_RUNTIME_DIR/edgeloop-ai/pairing.json`). Choose the companion in the Ollama model menu:

| Companion | Model |
|---|---|
| Nova | `nova-narrative-f29-v011:latest` |
| Daisy | `daisy-narrative-f29-v014:latest` |
| Evelyn | `evelyn-narrative-f29-v013:latest` |
| Celeste | `celeste-narrative-f29-v012:latest` |

All four share the same base weights (`qwen3.5:9b`), so `ollama ps` keeps showing whichever companion loaded first. That's expected. The request itself carries the selected model.

### Manual alternative, without systemd

Use one terminal for each:

```bash
OLLAMA_HOST=127.0.0.1:11435 OLLAMA_MODELS=~/.ollama/models ollama serve
tools/serve-ai.sh      # prints a one-hour pairing token; paste it into the companion panel together with ws://127.0.0.1:8768/observe
tools/serve-local.sh   # page on http://127.0.0.1:8770/
```

To check Ollama, run `tools/ollama-status.sh`.

Companion data (Story Memory, journal, selection) is stored in `.ai-data/` in this checkout. That's your real data. For a throwaway run, start the observer with `EDGELOOP_FORK_AI_DATA=/some/empty/dir`.

## Simulator-only testing (no physical device)

Steps:
1. Start the services as above.
2. Accept the age gate and skip the wizard.
3. Heart-rate card → **Manual Simulator** → set the slider → **Engage**.
4. Connect no toy. In the browser, do not grant any Bluetooth, serial or Handy permission.

Limits:
- A session can't start without a toy. The transport stays at "WAITING FOR … TOY", because the engine requires a connected toy, and the simulator only stands in for the heart-rate sensor.
- In the browser, simulator-only testing therefore covers the companion, chat, Director cards, video loading and the UI while IDLE.
- Running sessions, pause/resume, Edged, mode changes and emergency stop are covered by the automated suites. These use a mocked Handy and never touch a device:

```bash
cd ~/projects/edgeloop-ai-fork
node tests/fork/upstream-sync-browser.mjs   # all play styles, video+funscript, pause reasons, emergency stop, read-only chat
node tests/fork/browser.mjs                 # running session, pause/resume, stop, AI disconnect independence
node tests/fork/player-workspace-browser.mjs # player open/close, Theater, Fullscreen emergency stop, media-load dialogue
node tests/fork/character-browser.mjs       # portraits, Director mission card, emergency accessibility
node tests/fork/character-menus-browser.mjs
.venv/bin/python -m pytest -q               # full Python suite (2971)
npm test                                    # engine JS (1477)
node --test tests/fork/*.test.mjs           # companion JS (75/76, known alias-count failure)
```

These suites use mocked Ollama, their own fixture servers, temporary AI data and no pairing file. They refuse the desktop stack's ports (8770, 8768, 11435) and any port already in use, and their pages cannot reach other local ports, so they are safe to run while the desktop stack is up. Two suites that share a port can't run at the same time; the second one fails at start.

## Before any supervised hardware session

All of these must hold:
- [ ] The simulator checklist below is done, with no open safety item.
- [ ] Emergency stop was tried in the UI while IDLE and during a reply. It should take about 50 ms and leave status IDLE with outputs 0.
- [ ] The device is in hand, with a physical way to cut power or remove it that doesn't depend on the browser.
- [ ] Start with the lowest Max speed / intensity setting and a short duration. Use one device at a time.
- [ ] You know where the global **Emergency stop** button is (top right of the companion header).
  - In **Theater** and **Fullscreen** there is also an **Emergency stop** at the top centre of the video. It uses the same safety stop.
- [ ] The upstream hardware changes have not been checked on real devices yet. Check them one at a time:
  - The Handy firmware 4 absolute position / HSP
  - Intiface/Lovense touch modes
  - T-Code script follow
  - Finisher hold-at-max
  - adjustable Crawl %
- [ ] The companion is optional. Stopping Ollama or disconnecting the companion mid-session must not affect the session.

## Feature checklist

AI companions:
- [ ] Each of Nova, Daisy, Evelyn and Celeste loads its model, portrait and voice. Switching between them works.
- [ ] A direct question gets a grounded answer: the right BPM, simulated, and IDLE/RUNNING.
- [ ] Opening, Arrival, mission cards, Character Cards and Closing appear when eligible. A mandatory event (Opening, Closing, mission) isn't displaced by a Character Card.
- [ ] An earlier question is not answered again when a card fires afterwards (card-history separation).
- [ ] Chat never blocks the session controls. A long reply can be cancelled.

Sessions and protections:
- [ ] All play styles are listed, including Bratty Tease and Script (video player).
- [ ] Pause, resume, Stop, Edged and **Emergency stop** work. The companion speaks a safety notice after an emergency stop and makes no model call for it.
- [ ] Asking the companion to start, stop or change anything changes nothing in the engine.
- [ ] Stopping Ollama (`systemctl --user stop edgeloop-ai-ollama`) mid-chat leaves the page and the emergency stop working.

Video/script:
- [ ] The player stays closed until you press the **Player** header button: loading media, starting a session or a Director line never opens it.
- [ ] Open the player, then load a video plus `.funscript`. The play style switches to Script, and the companion does not comment on it as your choice.
- [ ] **✕ Close player** returns to the conversation layout. The session, companion, chat and loaded video are kept.
- [ ] Playback stays paused until a heart-rate source and a toy are ready. That's upstream behaviour.
- [ ] Theater and Fullscreen open and close (Exit / Esc). The session controls move into the overlay.
- [ ] Note any Director lines that appear when a video is loaded (see the issues below).

UI:
- [ ] Companion portrait and dialogue stay readable at 1920, 1366 and a phone width (390).
- [ ] Session controls stay reachable in every view.

## Known issues to watch (not fixed in this consolidation)

Video player and Director (fixed on `feature/player-workspace`):
1. Theater was clipped to the Session column. It now covers all three columns below the companion header; Esc returns.
2. Fullscreen hid the companion's Emergency stop. An Emergency stop now sits inside the video stage in Theater and Fullscreen.
3. The player was narrow. When opened, the video is now shown large in the centre column above a compact chat.
4. Loading a video + funscript gave unsolicited "Script mode" Director lines. The switch to Script came from loading media, but was treated as the user's own selection. It is now recorded as context only. Choosing a play style yourself is still acknowledged.

Grounding (dialogue quality), to be investigated separately:

5. Invented participant or session history.
6. Unsupported physiological interpretation. Example from live checks: "you're running a bit warm for an idle session" at a simulated 98 BPM.
7. Unsupported performance or device assumptions. Example: "the hardware is just humming along" with no toy connected.
8. Character Card intent not always followed. A related slip: Daisy once addressed the participant as "Daisy".

Tests (already failing before this merge, not weakened):

9. `presentation.test.mjs`: the alias count is 26, the test expects 25.
10. Browser scripts out of date with the current UI or the retired Director 1 events:
    - `event-intelligence-browser.mjs`, `context-intelligence-browser.mjs`, `session-journal-browser.mjs`, `memory-navigation-browser.mjs`, `event-reliability.mjs`
    - `event-reliability.mjs` now stops at the removed `#openParamsBtn`; the Params modal opens from `#sessionParamsHeaderBtn`
    - `live-browser.mjs` (manual live smoke) fills the pairing form that desktop pairing now replaces
    - upstream `tools/smoke.js`: two steps are out of date upstream

## Logs and reports

- Services: `journalctl --user -u edgeloop-ai-ollama -u edgeloop-ai-observer -u edgeloop-ai-web`
- Engine session log: opt-in, download it from History.
- Companion diagnostics: Director → Runtime diagnostics, in the companion panel.
- Reports:
  - `~/Work/edgeloop-f29-preview/UPSTREAM_SYNC_IMPLEMENTATION_20261105.md`
  - `~/Work/edgeloop-f29-preview/CONSOLIDATION_20261105.md`
  - `docs/fork/character-cards-v050/README.md`
  - `docs/fork/card-context-separation/README.md`

## Stopping

```bash
tools/launch-desktop.sh stop         # or the "Stop EdgeLoop AI" menu entry
tools/launch-desktop.sh status       # all units inactive
ss -ltnp | grep -E ':(11435|8768|8770)\b' || echo "ports free"
```

If you used the manual alternative, press Ctrl+C in each terminal.
