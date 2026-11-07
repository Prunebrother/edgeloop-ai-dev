# Changelog

## v0.6.0-rc3 — Windows installer recovery fixes (pre-release)

Windows-only packaging update. Models and application behavior are unchanged; the Linux download remains v0.6.0-rc2.

- Windows setup restores the working backup before retrying an interrupted repair, and rolls back if Python preparation or settings configuration fails.
- Previous installations and downloaded parts are kept until Windows setup finishes installing shortcuts and uninstall information. Interrupted cleanup cannot turn a partially deleted backup into a recovery target.
- Truncated Windows downloads retain their partial files and resume on retry. Resumed responses are checked before data is appended.

## v0.6.0-rc2 — test build with Windows installer (pre-release)

<!-- Release candidate for testers, published on the dev repository only. Hardware testing is still to do; v0.5.0 was never released and is folded into this version. -->

- **Windows installer (experimental).** `EdgeLoop-AI-Setup-v0.6.0-rc2.exe` installs the complete app for one Windows user without administrator rights: the same companions, model, Ollama (with NVIDIA CUDA support) and portable Python as the Linux bundle. Start menu shortcuts start and stop the local services; uninstalling keeps your data. Tested on Windows without a GPU or toys; real-hardware testing is still to do. The setup program is not code-signed yet. See INSTALL.md.
- On Windows, the observer and web server claim their ports exclusively, and the web server refuses Windows-style backslash and colon paths.
- Otherwise identical to v0.6.0-rc1, below.

## v0.6.0-rc1 — test build (pre-release)

- **AI Settings Control (new, off by default).** When you turn it on in the *AI Settings Control* panel, the companion may change a few session settings itself, in character: play style, game, endgame, the orgasm toggle, intensity inside a band you set, and pause or stop. Every request passes a local gate (allowlist, your limits, rate limits, a fresh heart-rate signal and a ready toy) and then goes through the same path as the on-page controls. Each change shows a chip with Undo and is announced by the companion with a short in-character card. *Own changes* sets how often the companion may change something on its own initiative (Never, Rarely, Sometimes (default, at most every 5 minutes) or Often); changes you ask for in chat are not held back by it. The companion can never start or resume a session, reset it, change the duration, heart-rate limits, calibration, devices or the speed window. Emergency stop revokes AI control for the rest of the session. See SAFETY.md.
- **Player interactions.** The companion reacts when you open the video player, select a video or start it, through the same Director queue as other events.
- **Player workspace.** The video player moved to the centre column, with Close player, a fixed Theater mode and an Emergency stop inside the player stage, so it stays reachable in Theater and Fullscreen.
- Fix: UI files are always revalidated, so an old cached stylesheet can no longer break the dashboard layout (for example the chat not scrolling) after an update.
- Fix: the companion service restarts cleanly even when the previous run's port is still closing.
- Built on EdgeLoop 1.1.4.31 (previously 1.1.3). New in the original app:
  - a video player that can follow a funscript, with Theater and Fullscreen
  - the Bratty Tease play style
  - an Edged button that pauses and counts an edge
  - adjustable Crawl speed
  - Finisher holds at the heart rate you set
  - No Nut November (renamed from NNN practice), with a midnight day roll
  - an opt-in session log you can download from History
  - updated drivers for The Handy, Intiface/Lovense and T-Code
  - a warning when EdgeLoop is not the focused window
  - Play Style and Session Endgame as compact cards
- The companion follows the new page layout.
- Companions now see Bratty Tease and video/script sessions, and the new card names (Simple Ramp, Ruin & Leak, No Nut November and others).
- Companions can tell why a session is paused. An Edged stop counts as an edge, not a pause, so it is not described as a break.
- Character Card expansion: 48 companion Character Cards, twelve each for Nova, Daisy, Evelyn and Celeste, alongside the 19 Common Cards. The Director deals them as before.
- Earlier conversation reaches a card prompt as background, separate from the card's own instruction, so companions are less likely to answer an old message again.
- Not included: upstream's agent link (AI control through a share link) and starting without a heart-rate sensor. The heart-rate requirement is unchanged.

## v0.4.0 — companion conversation update

- Four current companions: Nova, Evelyn, Daisy and Celeste, rebuilt with revised character prompts. Nova is the default for new installs; existing selections of older models need choosing again.
- The Director card deck is on by default: companions occasionally bring in a short story or character moment. There is no settings switch yet; it can be turned off per companion in `deck-settings.json` in the data folder.
- Story Memory now keeps what the participant said and no longer stores the companion's own lines, which reduces repeated phrasing. Only the participant's previous message is replayed, as background.
- Reply cleanup: removes a restatement of your message at the start of a reply, unwraps quoted replies, drops stage narration between quoted speech and caps reply length.
- Smaller download (about 9 GB): a single base model (qwen3.5 9B). The qwen3 8B weights are no longer included.

## F2.10 — public release preparation (unpublished)

Separate source snapshot, privacy exclusions, public documentation and issue templates. No private Git history, model weights, private sessions or character artwork is included. Upstream licensing and acknowledgments are retained. Publication remains gated by validation and provenance findings.

## F2.8 series — context and memory

Context compilation and budgets, narrative objectives, durable sourced facts, character-scoped Story Memory, opt-in Session Journal and permission-controlled historical retrieval. Significant-memory extraction and experimental Director initiative have current working-tree regression coverage; live quality remains under evaluation.

## F2.2–F2.7 — local companion

Self-contained read-only observer, local Ollama integration, streamed conversation, model selection, bounded Director scheduling, event intelligence, grounding safeguards, character menus and expression presentation, launcher and pairing support. Thinking remains disabled.

## Original EdgeLoop 1.1.3

Inherited browser engine, device drivers, physiological calculations, session rules, protections and manual controls. See the preserved [upstream changelog](docs/upstream/CHANGELOG.md) and [attribution](NOTICE_FORK.md). Historical upstream release claims are not new validation of this fork.
