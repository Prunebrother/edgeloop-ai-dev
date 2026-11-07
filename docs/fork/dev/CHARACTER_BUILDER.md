# Character Builder

Players create their own world, character, portrait and card deck. EdgeLoop validates
the result, composes a versioned package and runs that character on an installed Ollama
model, with its persona replacing the model's built-in identity. Model weights are not
rebuilt.

Status: target release v0.7.0. Built on `feature/character-builder` from
`experiment/ai-companion` `ec5b203`, then combined with v0.6.0-rc3 (`7c42ed5`) on
`integration/nov9-character-builder` for the November 9 live test. The commit that passes
that test becomes the v0.7.0 candidate.

## Where things live

| Piece | Location |
| --- | --- |
| Schemas, validation, Character Composer, library, preview | `companion_ai/character_builder.py` |
| Persona replaces the Modelfile SYSTEM | `OllamaProvider.persona_system` in `companion_ai/llm.py` |
| Activation, metadata overlay, restore after restart | `ModelManager.select(..., character=)` and `overlay()` in `companion_ai/conversation.py` |
| Memory, deck, pacing and journal scope | `ConversationService.adapter_scope()` and `sync_character_deck()` |
| Protocol command | `character_builder` in `ai_observer/protocol.py` |
| Server handler and portrait route | `ai_observer/server.py` (`/character-art/<sha256>.<ext>`) |
| Editor workspace | `src/js/ai/character-builder.js`, opened from **Character Builder** in the model picker |
| Per-character AI Settings | `selectProfile()` in `src/js/ai-settings/control.js`; storage key `edgeloop_ai_settings:custom.<id>` in `src/js/app.js` |
| Per-character event preferences | `relevance_for()` in `companion_ai/event_intelligence.py`; `relevance_identity()` in `companion_ai/conversation.py` |
| Portrait overlay | `setCustomCharacter()` in `src/js/ai/artwork-manifest.js` |
| Fixture | `tests/fixtures/character-builder/` (Saltglass Reach world, Wren Calloway) |

Player data is stored in the observer data directory (`.ai-data` by default):

```
character-builder/
  worlds/<world-id>.json             source; reusable by any character
  characters/<character-id>.json     source; names its world and holds its deck
  art/                               portrait inbox: the player puts images here
  art-store/<sha256>.<ext>           content-addressed copies made by the composer
  packages/<character-id>/<sha12>.json   composed packages, one file per version
  active.json                        the activated package, or null
```

## Sources

World (`schema_version` 1): `id` (`a-z0-9-`, 24 characters), `name`, `setting` (1200),
`lore` (3000), `rules` (up to 8 lines of 200 characters).

Character (`schema_version` 1): `id`, `world`, `name`, `short_name` (one capitalised
word; cards speak as this name), optional `age` (18 or over), `personality` (1200),
`voice` (800), `relationship` (600), `model` (any installed model; the default is the
shared base `huihui_ai/qwen3.5-abliterated:9b`), `portrait` (`file` name in the art
inbox, `fit`, `position`), `deck`, and `revision`, which goes up automatically each time
a save changes the content.

Deck: `shared` is `lifecycle` (the default) or `lifecycle+routine`, plus up to 16
`cards`. A card is:

```json
{"id": "tide-reading", "theme": "tide-lore",
 "brief": "What the model should do (max 400)",
 "occasion": "Optional: what has just happened (max 160)",
 "when": {"min_seconds": 60, "max_seconds": null, "min_edges": null, "max_edges": null,
          "requires_hr": false, "hr_trends": null, "requires_conversation": false,
          "requires_story_welcome": false, "statuses": ["RUNNING", "RAMPDOWN"]},
 "repeat": true, "enabled": true}
```

`when` is the existing deck `Eligibility` model, so the Director applies the same rules
it uses for built-in cards. `theme` becomes the card's intent. Disabled cards stay in the
source but are left out of the package.

## Package format (`edgeloop.character-package`, version 1)

```json
{
  "format": "edgeloop.character-package",
  "format_version": 1,
  "id": "wren-calloway",
  "revision": 1,
  "identity": "custom.wren-calloway",
  "model": "huihui_ai/qwen3.5-abliterated:9b",
  "world": { "...validated world..." },
  "character": { "id", "name", "short_name", "age", "personality", "voice", "relationship", "world", "schema_version" },
  "portrait": { "sha256", "file": "<sha256>.png", "media_type", "fit", "position" },
  "persona_system": "You are Wren Calloway, an adult aged 34 ...",
  "deck": { "shared": "lifecycle", "cards": [ "...runtime Card objects..." ] },
  "content_sha256": "<sha256 of the canonical JSON of everything above>"
}
```

- **Deterministic.** The composer has no clock, randomness or environment input. It
  normalises line endings and outer whitespace, sorts cards by ID and hashes canonical
  JSON (sorted keys, no spaces). The same sources and portrait bytes always give the same
  bytes and hash. Card order and CRLF versus LF do not change the result.
- **Versioned.** `format_version` is the schema version. `revision` counts the
  player's saves. `content_sha256` identifies an exact build. `active.json` points to an
  exact hash.
- **Validated on load.** `load_package` recomputes the hash. A package edited after
  composing is rejected. So is one whose cards target another audience, or any card that
  is not a custom `normal` card.
- **Runtime card IDs** are `<character-id>.<card-id>`. Every card's audience is the
  custom identity.

## How a custom persona and world reach the prompt

The built-in companions all run on one base model. Daisy, Evelyn, Nova and Celeste
differ only in their Modelfile `SYSTEM`; none has an adapter. Ollama uses a model's own
`SYSTEM` only when a request has no system message.

Decision: with a custom character active, `OllamaProvider.persona_system` is set and
every request carries a system message that starts with the composed persona. This
includes requests that previously sent none, such as the AI Settings decision. The
persona replaces the embedded identity; it is not appended to it. The runtime rules from
the prompt compiler follow it as before. The same text is overlaid on the model
metadata, so narrative canon, context budgets, the memory curator and grounding checks
all see the persona as "the embedded identity".

Authored text stays in its section:

- World and character fields go only into `persona_system`, in labelled lines.
- Card `brief` and `occasion` go only into the existing card turn (`card_instruction`).
- Section markers such as `### `, `SYSTEM`, `<|im_start|>` and `[INST]` are rejected
  in briefs and world text.

Proof: unit tests run Wren on Daisy's model and check the wire request. The live smoke
did the same with the real `daisy-narrative-f29-v014` model: Wren answered as Wren, with
no Daisy canon, and plain Daisy came back afterwards on the same model.

## Workspace

The model picker stays the way in. **Character Builder** there hides the conversation and
opens the editor in the same column (on a phone it switches to the chat view first).
**Back to chat** shows the conversation again. The conversation stays in the page and
nothing is re-requested, so its history and the active character are exactly as they
were.

## Per-character preferences

- **AI Settings Control** is stored per custom character under
  `edgeloop_ai_settings:custom.<id>`, and the built-in companions keep the original
  key. A custom character starts with it off even if it is on for the built-ins. The
  player opts in through the existing AI Settings panel, which says which character the
  setting applies to. On a character switch the control loads that character's stored
  setting, or the off default, clears any pending request and restarts pacing only if
  enabled.
- **Event preferences** are keyed `custom.<id>`. A custom character without stored
  preferences uses the normal defaults (every category at 1). It never uses the
  preferences of the built-in companion whose model it runs on. Settings show it as
  "Custom character: <id>".

## Limits

- **16 cards per deck** (`MAX_CARDS`). The builder shows "N of 16 cards" and disables
  **Add card** at 16.
- **16 KiB per message.** The observer closes a socket (1009) on a larger inbound
  message, so the client counts UTF-8 bytes, not characters. World and character are
  saved as separate messages, and the builder shows the size of each. Before saving it
  checks both, so an oversize character never leaves a half-saved pair. The error
  explains that long text can reach the limit before 16 cards.
- **Portraits** come from the art folder the builder shows (PNG, JPEG or WebP, up to
  8 MB). There is no direct upload yet.

## Portrait route

`/character-art/<sha256>.<ext>` has no pairing token, so it is restricted:

- it answers only a loopback peer (`127.0.0.1` or `::1`), and anything else gets 404;
- the observer binds to 127.0.0.1, and the existing Host and Origin checks still apply;
- the file is served only if its SHA-256 matches its name and the detected image type
  matches the extension, so a renamed SVG or other file is refused.

Knowing a hash grants nothing beyond what is already on the local disk.

## What stays with the engine

Custom cards are dialogue and story briefs only. The card schema has no action, setting
or device field, and unknown fields are rejected. Briefs and occasions that ask to
change speed, intensity, stroke, mode, settings, device, session state or game, or that
mention emergency stop, are rejected with a pointer to the separate action interface.
Session state, device output and emergency stops remain the engine's; the existing
grounding checks (`read_only_control_claim`) still apply to every reply. Characters must
be adults: `age` must be 18 or over, and explicit minor descriptors are rejected.

## Deck composition

A custom character's runtime deck contains:

- the built-in shared lifecycle cards: `opening`, `closing`, the three `arrival-*`
  cards, and the `edges-3/7/10` milestones;
- the built-in shared routine cards (edge count, duration, heart rate), only with
  `"shared": "lifecycle+routine"`;
- the character's own enabled cards.

Built-in personal cards never reach a custom character, and custom cards never reach
built-in companions. Theme weight works through the existing shuffle. Each eligible card
is drawn once per cycle, so four eligible `tide-lore` cards against one `dry-tease` card
give a 4:1 ratio in every full cycle (tested).

## Memory isolation

Scope is `provider:url:model#character=<id>`. Conversation history, Story Memory,
deck settings, pacing profiles and the Session Journal companion (`custom.<id>`) all key
on it. The scope is therefore separate from the built-in companion on the same model and
from every other custom character. Editing a character keeps its ID and its memory.

## Try it in the simulator

1. Start the dev Ollama and the observer as usual, and open the app.
2. Start a simulated session: HR Monitor → Manual Simulator, connect a Handy (a real one
   or the browser fixture mock), then Play.
3. Pair the AI companion, then press **Character Builder** next to the model picker.
4. Copy `tests/fixtures/character-builder/wren.png` into the art folder the builder shows.
   Go back to chat and reopen the builder.
5. Fill in the world and character, for example from the fixture JSON files, choose
   `wren.png`, and add cards.
6. Press **Preview**. It saves, then shows any validation errors with field paths, or
   the persona, cards, theme counts, shared lifecycle cards and portrait.
7. Press **Activate**, then **Back to chat**. The character panel shows Wren, and the chat
   runs on her persona.
   After the opening card, custom cards are drawn once the session passes their `when`
   rules (the fixture cards need 60 s).
8. To return to a built-in companion, choose its model in the picker and press
   **Switch model**.

## Conditions the editor does not show

The editor edits time, edge, conversation and enabled conditions. Other conditions
written in a character file (`requires_hr`, `hr_trends`, `statuses`,
`requires_story_welcome` and the rest) are listed on the card as "kept as written". They
are sent back unchanged when the deck is saved.

## Follow-ups

- A set of portraits for different expressions (one portrait serves all of them now).
- Uploading a portrait directly instead of using the art folder.
- Builder controls for heart-rate and story conditions.

## Tests

- `tests/ai/test_character_builder.py` (46): composer determinism and versioning,
  malformed cards, artwork paths and content, adult checks, save and reopen, revisions,
  symlinks, persona replacement on the wire, memory isolation, restore after restart,
  deck composition, the theme ratio, a Director draw in the event replay, the full
  editor flow over the observer protocol, per-character event preferences, the
  loopback-only portrait route, and conditions kept on reopen and resave.
- `tests/fork/character-builder.test.mjs`: the portrait overlay, URL safety, kept
  conditions and UTF-8 message sizes.
- `src/js/ai-settings/control.test.js`: per-character AI Settings profiles.
- `tests/fork/character-builder-browser.mjs`: the in-app flow with the Manual Simulator,
  mocked Handy and mocked Ollama. It covers the workspace, the card count and size
  meters, a malformed card, preview and activation, AI Settings off for the custom
  character and its opt-in, its event-preference entry, chat kept across the workspace,
  a custom card draw, the 16-card cap, an oversize save refused, conditions kept on
  resave, and the switch back to Daisy with her own AI Settings. Run it with `node tests/fork/character-builder-browser.mjs`;
  in a worktree, set `EDGELOOP_TEST_PYTHON` or symlink `.venv`.
- `tests/fork/character_builder_smoke.py`: opt-in live run on real models
  (`EDGELOOP_LIVE_ACCEPTANCE=1`, port 11435).
