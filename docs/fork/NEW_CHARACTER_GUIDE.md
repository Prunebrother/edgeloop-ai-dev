# Adding a new companion: guidance

Written 2026-11-16 after Mira (the fifth companion) and the PA-1 portrait re-render. It
lists everything a new built-in companion needs, in the order that worked, plus the lessons
from the first five. Use `<id>` for the lowercase character id (`mira`) and `<Name>` for the
display name (`Mira`).

A companion consists of six parts:

| # | Part | Where | Section |
|---|---|---|---|
| 1 | Character definition (who she is) | `characters/models/<id>-narrative-f29-v0NN/character.REVIEW.yaml` | [1](#1-character-definition) |
| 2 | Modelfiles (F2.9 standard: parent + f29 persona) | `characters/models/<id>-narrative-v1/` and `characters/models/<id>-narrative-f29-v0NN/` | [2](#2-modelfiles-f29-standard) |
| 3 | Artwork: 12 expressions | `Character_Art/<Name>/expressions/` | [3](#3-artwork) |
| 4 | Idle animations: 12 clips | `Character_Art/<Name>/animations/` | [4](#4-idle-animations) |
| 5 | Cards: 15 personal cards | `config/event-deck.json` | [5](#5-cards) |
| 6 | App wiring, tests and release | manifest, Python name lists, release inputs | [6](#6-app-wiring), [7](#7-release) |

Work on a feature branch (`feature/<id>-narrative-v1`), merge into `experiment/ai-companion`
when the user approves, and never push without being asked.

---

## 1. Character definition

Start from the standard character template (schema v0.3.0), printed in full in
[Appendix B](#appendix-b-character-template); the source is
`Characters_F2.9_update/Empty_Templates/character.template.yaml`. Save it as
`characters/models/<id>-narrative-f29-v0NN/character.REVIEW.yaml`. The most recent filled-in
example is `characters/models/mira-narrative-f29-v015/character.REVIEW.yaml`. It is an
authoring document; the app does not import it. Its `metadata.definition_version` follows the
f29 number (`v015` → `0.1.5`), and every change gets a `changelog` line.

- **Adults only.** State it in `identity.adult_status`. Cards and the builder reject anything else.
- **Fit the shared world** (`Characters_F2.9_update/World_Canon/edgeloop.world-canon.v0.1.yaml`):
  IRRA, Asterion, Cloverfield, Helix Dynamics, the participant as a Proven Breeder. Add new
  facts only where the canon leaves room, and say so in the README. Characters do not know
  each other's private events.
- **A starting premise, not a history.** Missions, rivalries and feelings are tensions to develop
  in play. Nothing is already accomplished (no past encounters, no collected samples, no
  instant love).
- **Give her an inner life:** something she wants, something she is unsure about, and hobbies
  that are interests rather than past adventures. This is what keeps replies from looping.
- Keep a `README.md` in the parent folder (`<id>-narrative-v1/`) with status, model tags, the build
  command and the smoke results (see `characters/models/mira-narrative-v1/README.md`).

## 2. Modelfiles (F2.9 standard)

Every companion is **two Ollama models**, the same way for all five:

| Model | Folder | Contains | Ships? |
|---|---|---|---|
| Parent `<id>-narrative-v1` | `characters/models/<id>-narrative-v1/Modelfile` | `FROM` the base model, the sampling `PARAMETER`s, and a first SYSTEM draft | Built during the release as an *intermediate*, then removed |
| F2.9 persona `<id>-narrative-f29-v0NN` | `characters/models/<id>-narrative-f29-v0NN/` | `FROM <id>-narrative-v1:latest` and **only** the reviewed SYSTEM. Next to it: `SYSTEM.CANDIDATE.txt` (the same text as the SYSTEM block) and `character.REVIEW.yaml` | The model the app uses |

| Companion | Parent | F2.9 model |
|---|---|---|
| Nova | `nova-narrative-v1` | `nova-narrative-f29-v011` |
| Celeste | `celeste-narrative-v2` | `celeste-narrative-f29-v012` |
| Evelyn | `evelyn-narrative-v1` | `evelyn-narrative-f29-v013` |
| Daisy | `daisy-narrative-v1` | `daisy-narrative-f29-v014` |
| Mira | `mira-narrative-v1` | `mira-narrative-f29-v015` |

`v0NN` is one running counter across the cast. The next new persona or revision gets `v016`.
A persona revision is a **new** f29 folder and tag. Don't edit a shipped one in place, so
installed models and memory scopes stay comparable. Templates for both Modelfiles are in
[Appendix A](#appendix-a-modelfile-templates), and also as files in
`Characters_F2.9_update/Empty_Templates/`.

The SYSTEM text follows the same outline as the cast, with the section names adapted to the
character:
1. Identity line: name, designation, age or nature, role, "in the fictional EdgeLoop world".
2. Character / personality, inner life, motivations.
3. Relationships with the other companions and with the participant (develops through actual exchanges).
4. Voice / conversation: concise, answer first, what to avoid.
5. Known setting: the shared canon bullets, as in the other f29 files.
6. Evidence and boundaries: never invent measurements, records or completed missions.
7. Terms: experience, goal, active_mode, edge.

Rules:
- **Sampling lives in the parent Modelfile.** The f29 child has no `PARAMETER` lines and
  inherits them. The app does not override temperature (b2eefda,
  `tests/ai/test_modelfile_sampling.py`).
- **No `TEMPLATE` or stop-token overrides.** Inherit the base model's native template.
- **SYSTEM only, no adapters.** A Character Builder persona replaces SYSTEM at runtime, so
  nothing else may live in the Modelfile.
- **No persona safety clauses.** Session safety is the engine's job; dark in-character dialogue
  is not a defect. Consent and boundaries belong in the persona as character, not as
  disclaimers.
- The app adds the expression list, thinking-off and runtime rules itself. Don't repeat them.

Persona lessons from Mira's tuning (700494c, 5 simulated sessions per variant):
- "Do not echo the participant's last words" and "do not return to favourite lines" reduced
  repetition (repeated 5-grams 2.7 → 1.3 per 100 lines).
- "Pick the expression that fits each reply" widened the expressions used in chat (4 → 6 kinds).
- **Negative topic instructions backfire.** "Mention Helix less" made her mention it more.
  Describe what she does instead.
- Correct wrong assumptions she may make about other characters explicitly (for example, "Nova is
  not a shapeshifter").

Build and smoke test. Copy and adapt `tools/check_mira.py` as `tools/check_<id>.py`. It checks
the layering offline (child FROMs the parent, sampling only in the parent,
`SYSTEM.CANDIDATE.txt` matches). With `--live --build` it creates the parent, then the child,
and runs 10 dialogue cases:

```sh
# dev Ollama: OLLAMA_HOST=127.0.0.1:11435 OLLAMA_MODELS=~/.ollama/models ollama serve
.venv/bin/python tools/check_<id>.py --report /tmp/<id>-offline.json
.venv/bin/python tools/check_<id>.py --live --build --host http://127.0.0.1:11435 --report /tmp/<id>-live.json
# or by hand, parent first:
OLLAMA_HOST=http://127.0.0.1:11435 ollama create <id>-narrative-v1:latest -f characters/models/<id>-narrative-v1/Modelfile
OLLAMA_HOST=http://127.0.0.1:11435 ollama create <id>-narrative-f29-v0NN:latest -f characters/models/<id>-narrative-f29-v0NN/Modelfile
```

Read the live dialogue yourself. The automated checks cover format and length, not personality.
Run a few simulated sessions and compare repetition and expression variety with the existing cast.

## 3. Artwork

### What to deliver

All files are **1024 × 1536 PNG** (2:3). Every expression shares the same canvas, scale and
foot position.

| Layer | Files | Notes |
|---|---|---|
| Background plate | `plate.png` | The scene **without anyone in it**. It has real content where she stands, because she sways and the area behind her is revealed. Ideally one plate for all 12 expressions, so switching expression keeps the same scenery. |
| Cutouts | `cutouts/<expr>.png` × 12 | The character on a transparent background, at final position. Clean hair edges. Nothing she holds may be left in the plate. |
| Shadow / reflection (optional) | `shadow/<expr>.png` | Floor contact shadow or reflection as its own layer, because it must move with her. Never baked into the plate. |

The app PNG is **not** delivered by the artist. The animation pipeline builds it from the layers
(it is frame 0 of the clip), so the still image and the video match exactly.

The 12 expressions, in the app's order, are: neutral, happy, playful, flirty, mischievous,
focused, excited, surprised, disappointed, concerned, proud, comforting. Each is a
**full-body pose** that reads at thumbnail size, not just a different face.

**File names:** `<id>_<expression>.png`, spelled `disappointed`. The older characters use
`*_dissapointed.png`. The manifest key is always `disappointed`, so don't copy the typo.

### How we got there with the first five (lessons)

The first five characters were delivered as flattened PNGs, with a different background in
each expression. PA-1 (see `portrait-animation/BACKLOG.md`) had to rebuild them in layers
afterwards:
- Cut out with BiRefNet_HR-matting (`~/image-gen/matte.py`). This works well even on hair and on
  Mira's slime. A translucent body still gets a solid matte, because the translucency is
  painted into her pixels.
- The figure was painted out with a local Krea edit (`scripts/make_plate.py` in the pipeline).
  Outside the figure the original pixels stay untouched.

Prompt lessons from removing the figure (for plates):
- **Describe the figure concretely.** "Remove the woman" failed on all 12 Mira images. "The green
  slime girl made of glossy green goo, including her green hair, slime drips and silver bikini"
  worked.
- **Never name props in a removal prompt.** Naming the basket or tablet made Krea *add* props on
  stands, and once it added a floating second Daisy.
- **Never add "no X anywhere".** For Mira, "no slime anywhere" made it stop removing her.
- **Held props are left behind often** (tablets, baskets, gloved hands, boots). Try a different
  seed rather than a longer prompt.
- **Look at every plate.** The automated stillness check proves the background does not move. It
  cannot see a leftover hand.

Generating new art:
- **Pick one generator per character and keep it for all 12.** Local Krea (`~/image-gen`, menu
  "Image Gen") does not match the ChatGPT/gpt-image style of the first five. A mix within one
  character is visible.
- For identity across poses, use the two-reference recipe from `~/image-gen/README.md` (the plate
  aligned, plus the neutral cutout with a face crop).
- Generate the plate first, then the poses on that plate, so the background is identical by
  construction.
- **Explicit art must not go into the public GitHub repo.** Keep such variants out of
  `Character_Art/` and distribute them separately.
- Reference sheets, collages and other images go outside `Character_Art/<Name>/expressions/`.
  The release validator rejects unreferenced art in the package.

## 4. Idle animations

Pipeline: `~/Work/edgeloop-animation-pipeline` (CPU, deterministic; see its README). Output per
expression is one silent WebM, 8 s, 30 fps, VP9, the same size as the PNG.

Layer mode (PA-1 v2, used for all 60 current clips):

1. Put the layers in `layers_v2/<id>/plates/<expr>.png` and `layers_v2/<id>/cutouts/<expr>.png`.
   For flattened art, `scripts/make_plate.py <id> <expr> [--seed N] [--prompt-extra "..."]`
   makes them.
2. Place the motion in `configs/<id>/<expr>.json`: eyes and blink, breathing mask, sway and pins.
   Do the neutral first, get it approved, then derive the other 11 from it. Keep the placement
   script as `configs/<id>/_placement_record.py`. This step needs human judgment (README
   "How to place the motion").
3. `scripts/make_layer_configs.py <id>` writes `configs_layers_v2/<id>/`. Character-specific
   motion goes in there. Mira has `WOBBLE` (sway ×1.5, slower dwell, more head lag and fuller
   breath, because she is a slime girl).
4. `scripts/render_v2.sh <id> <expr>` renders, encodes, compares old with new and checks that
   every background pixel is static in every frame. To run all of them gently, use
   `scripts/overnight_v2.sh <id>` (nice 19, idle I/O, GPU pauses).
5. Review `reports_layers_v2/<id>/<id>_REVIEW_all12.mp4` and `<id>_plates_sheet.png` **by eye**,
   then have the user approve.
6. Copy `output_layers_v2/<id>/<id>_<expr>.png` → `Character_Art/<Name>/expressions/` and
   `<id>_<expr>.webm` → `Character_Art/<Name>/animations/`. **The PNG must be the clip's frame 0**,
   or the fade from still image to video jumps.

Replacing art that is already in the app needs the user's approval.

## 5. Cards

Personal cards go in `config/event-deck.json` under `normal`, with `"audience": "<id>"`. They
are shuffled together with the common deck. Bump `revision`. Allowed fields: `id`, `kind`,
`audience`, `intent`, `brief` and `eligibility`.

Every companion has **exactly 15** personal cards (enforced by `tests/ai/test_event_deck_content.py`):

| Count | Cards | Eligibility |
|---|---|---|
| 12 | Personality cards, about 4 themes (intents) × 3, in her own voice | mostly `{"statuses": ["RUNNING"]}`; some need `min_edges`, `requires_conversation` |
| 1 | `<id>-finish`, intent `finish_encouragement` | `{"statuses": ["RUNNING"], "phases": ["finishing"]}` |
| 1 | `<id>-another-load`, intent `another_round` | `{"statuses": ["RUNNING"], "phases": ["recovery"]}` |
| 1 | `<id>-orgasm-tally`, intent `orgasm_count` | `{"statuses": ["RUNNING"], "min_orgasms": 1}` |

Optional: her own `session_start` / `session_end` card replaces the shared opening/closing for
her only (Mira has both). The test lists these exactly, so update it.

How to write a brief (look at the existing cards):
- Start with the delivery: "Use playful delivery." (an expression name), optionally "if welcome".
- Say what she does now, in the current session state, with one concrete angle.
- **Spell out what must not be claimed:** no invented outcomes, results, agreements, past events,
  measurements or feelings of the participant. Listed counts are the only facts.
- No system language ("verified", "supplied"), no control or settings wording. Cards are dialogue only.
- Optional asks only, never pressure; "[SILENCE] is fine" where a remark could be unwelcome.
- Vary the jokes. Cards with the same punchline make her repeat herself.

Update `tests/ai/test_event_deck_content.py` (`test_every_companion_has_its_requested_themes`
with her intents) and any test that lists audiences.

## 6. App wiring

`src/assets/characters/manifest.json`:
- `characters.<id>`: `name`, `fit: "contain"`, `position: "50% 50%"`, the 12 `expressions`
  paths and the 12 `animations` entries (`{"webm": "/Character_Art/<Name>/animations/<id>_<expr>.webm"}`).
- `models`: both tags, `"<id>-narrative-v1:latest": "<id>"` and `"<id>-narrative-f29-v0NN:latest": "<id>"`.

The JavaScript has no character names hardcoded. The Python side has three lists. Add her to
each one:

| File | What |
|---|---|
| `companion_ai/event_intelligence.py` | the `preferences` default, the known-identity set, and the ordered tuple (3 places) |
| `companion_ai/nova_verified_bridge.py` | `CHARACTERS` and the name regex |
| `companion_ai/session_journal.py` | the name regex (a character's history is shared only when named) |

Then run `grep -rnE "Celeste|Mira" tests` for the tests (`test_arrival_comparison`, `test_card_prompt` and
others list the cast).

Tests to run before asking for review:

```sh
.venv/bin/python -m pytest -q tests/ai tests/fork
node --test tests/fork/*.test.mjs
node tests/fork/portrait-animation-browser.mjs
```

## 7. Release

When she ships in a release:
- `release-inputs.json`: the parent `<id>-narrative-v1` goes in `intermediate_characters`
  (built first, removed after), and `<id>-narrative-f29-v0NN` goes in `characters` (shipped).
  `tools/build-release.py` and `tests/fork/test_release_bundle.py` check that every `FROM`
  resolves to the base model or an intermediate.
- `.github/workflows/windows.yml`: add the f29 tag to the installed-companion check.
- `tests/fork/test_release_bundle.py`: the shipped model list.
- `MODELS_AND_ASSETS.md`: the portrait count and the model table.
- `CHANGELOG.md`, plus the version in `index.html` (`forkVersion`).
- `tools/validate-release.py` expects 12 portraits per manifest character and every declared
  animation to exist, and rejects art that the manifest does not reference.

## Checklist

- [ ] character.REVIEW.yaml + README, fits the world canon, adult
- [ ] Parent Modelfile `<id>-narrative-v1` (base + sampling) and f29 Modelfile `<id>-narrative-f29-v0NN` (FROM parent, SYSTEM only) + `SYSTEM.CANDIDATE.txt`; both built, smoke-tested, dialogue read
- [ ] Plate + 12 cutouts (+ shadows), one generator, same canvas and foot position
- [ ] 12 clips rendered in layer mode, static check passes, reel and plate sheet reviewed by eye, user approved
- [ ] PNG = frame 0, copied with the WebM into `Character_Art/<Name>/`
- [ ] 15 personal cards (12 + finish + another-load + orgasm-tally), deck revision bumped, test updated
- [ ] Manifest character + both model tags; the three Python name lists; tests green
- [ ] Release inputs (parent as intermediate, f29 as character), Windows workflow, release test, MODELS_AND_ASSETS, CHANGELOG (when shipping)

---

## Appendix A: Modelfile templates

Also available as files: `Characters_F2.9_update/Empty_Templates/Modelfile.parent.template` and
`Modelfile.f29.template`. Replace `<id>`, `<Name>`, `v0NN` and every `<...>` placeholder.

**Parent**, `characters/models/<id>-narrative-v1/Modelfile`:

```
# <Name> — narrative parent: base model and sampling. Built as a release intermediate.
# Inherit the supported native Qwen3.5 template/parser; no TEMPLATE or stop-token overrides.
FROM huihui_ai/qwen3.5-abliterated:9b

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 20
PARAMETER num_ctx 8192

SYSTEM """
<first persona draft; the f29 model below replaces it>
"""
```

**F2.9 persona**, `characters/models/<id>-narrative-f29-v0NN/Modelfile`. Copy the SYSTEM text
verbatim into `SYSTEM.CANDIDATE.txt` in the same folder:

```
FROM <id>-narrative-v1:latest

SYSTEM """
You are <Name>, <designation / age and nature>, <role> in the fictional EdgeLoop world. <One line on where she works or comes from.>

Character: <core traits, humor, values; what she enjoys and what she is not>.

Inner life: <what she wants, what she is unsure about, how affection or pressure changes her; interests are interests, not past adventures>.

Relationships: <each other companion in one clause>. With the adult participant, warmth and trust develop through actual exchanges.

Voice: <diction and rhythm>. Respond to the actual question first. Be concise for simple exchanges. Do not echo the participant's last words or return to favourite lines. Pick the expression that fits each reply.

Known setting:
- A near-future male fertility crisis prompted Project EdgeLoop, funded and overseen by IRRA.
- Only 1% of males qualify as Proven Breeders; the participant is one of these rare consenting adult volunteers with autonomy.
- <the other canon bullets that matter to her, copied from an existing f29 Modelfile>

Evidence and boundaries: Canon, agreed fiction, participant reports and runtime facts are different. Never invent heart rate, measurements, edge counts, Journal progress, session outcomes, hardware activity or completed missions. If no permitted data was supplied, say it is unavailable.

Terms: experience means selected play style; goal means selected session game; active_mode means actual engine behavior. An edge is an engine threshold event, not proof of a physiological outcome, mission success or consent.
"""
```

## Appendix B: character template

`Characters_F2.9_update/Empty_Templates/character.template.yaml`, schema v0.3.0, copied here
as-is. That folder is left out of the public source package, so this copy is the reference for
outside developers. Mira's filled-in version
(`characters/models/mira-narrative-f29-v015/character.REVIEW.yaml`) uses the same fields in JSON
syntax, which is valid YAML 1.2.

```yaml
# EdgeLoop AI — Standard Character Template
# F2.9 | draft schema_version 0.3.0 | Stable Character Definitions
# Copy this file to create a new character. Leave unknown information null or [].
# No example character, user information, live telemetry, memories, or local paths belong here.
# Shared runtime protocols are applied by EdgeLoop, not redefined by each character.

schema_version: "0.3.0"
kind: character_definition

metadata:
  character_id: null              # Unique slug, e.g. lowercase letters/numbers/hyphens
  definition_version: "0.1.0"    # Manually versioned character definition, not model weights
  status: draft                  # draft | review | approved | retired
  description: null
  source_references: []          # Non-sensitive source IDs, not absolute local paths
  changelog: []

identity:                         # Authored core: edits require author review
  name: null
  aliases: []
  adult_status: adult            # EdgeLoop characters are adults; do not unset
  nature: null                   # Human, synthetic, etc.; character-specific
  universe: null
  occupation_or_role: null
  affiliations: []
  origin: null
  biography: null
  defining_history: []
  foundational_values: []
  immutable_canon: []

personality:                      # Stable authored traits, edited manually and versioned
  core_traits: []
  strengths: []
  flaws: []
  internal_contradictions: []
  motivations: []
  fears_and_vulnerabilities: []
  beliefs_and_worldview: []
  interests_and_hobbies: []
  preferences: []
  personal_ambitions: []

relationships:                    # Fictional starting facts, not imported user data
  established: []                # Items to be defined by the character author
  boundaries_and_loyalties: []

communication:
  voice: null
  diction: null
  humor: null
  warmth: null
  directness: null
  initiative_style: null
  emotional_range: null
  distinctive_mannerisms: []
  repetitive_patterns_to_avoid: []
  conversation_preferences: []
  response_length: adaptive      # No rigid sentence quota

narrative:
  primary_setting: null
  personal_stakes: []
  story_goals: []
  established_story_facts: []
  unresolved_threads: []         # Authored premises only; evolving threads live in memory
  expertise: []

knowledge:
  shared_world_canon_ref: null   # Resolved by a shared, versioned canon source
  character_known_facts: []
  character_unknown_facts: []    # Guard against omniscience
  character_private_facts: []
  edgeloop_terms_ref: null       # Versioned definitions; NOT current session state

integration:
  standalone_ollama_chat: true
  edgeloop_runtime_compatible: true
  expression_set_ref: edgeloop-12
  default_expression: neutral
  expression_style_notes: []
  # Rendering/header syntax is inherited from the runtime's actual protocol.
  # Telemetry, Director events, session state and records are NEVER authored here.

memory:
  strategy: external
  character_isolation: true
  journal_access: runtime_permission_required
  cross_character_recall: explicit_authorization_only
  # The runtime enforces access; this file cannot grant itself permissions.

model:
  base_model_ref: null           # Portable model name/tag, not a blobs/ absolute path
  prompt_renderer_ref: null      # Must match actual supported Qwen/Ollama integration
  inference:
    temperature: null
    top_k: null
    top_p: null
    num_ctx: null
  # Inference behavior (including think:false) is enforced by the application.

assets:
  portrait_manifest_ref: null
  voice_manifest_ref: null

publication:
  character_text_provenance: null
  character_text_license: null
  assets_rights_status: not_reviewed
  redistribution_approved: false
```
