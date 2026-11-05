# Changelog

## v0.5.0 — draft, unreleased

<!-- DRAFT: not tagged or published. Supervised feature testing and hardware checks are still to do before release. -->

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
- The companion follows the new page layout. The video player sits in the Session column, with Theater and Fullscreen for a larger view.
- Companions now see Bratty Tease and video/script sessions, and the new card names (Simple Ramp, Ruin & Leak, No Nut November and others).
- Companions can tell why a session is paused. An Edged stop counts as an edge, not a pause, so it is not described as a break.
- Character Card expansion: 48 companion Character Cards, twelve each for Nova, Daisy, Evelyn and Celeste, alongside the 19 Common Cards. The Director deals them as before.
- Earlier conversation reaches a card prompt as background, separate from the card's own instruction, so companions are less likely to answer an old message again.
- Not included: upstream's agent link (AI control through a share link) and starting without a heart-rate sensor. The companion stays read-only; the heart-rate requirement is unchanged.

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
