# Portrait animation backlog

## PA-1 Layered artwork: static background plate + moving character cutout

**Status:** DONE 2026-11-16 (all 60 clips swapped; see the status notes below). Reopened 2026-11-15 with a new approach (see "Revised plan" below). The first
attempt (regenerating the art as layers with Codex, then local Qwen/Krea) was dropped: Codex
was blocked by moderation on 7 poses and the local models did not match the original style.

## Revised plan (2026-11-15): cut the ORIGINAL art into layers

All 60 original expression PNGs (5 characters × 12) were cut out locally with
BiRefNet_HR-matting (`~/image-gen/matte.py`). The cutouts are the original pixels in their
original position; only the background is removed. User review of the overview sheet: "these
look great". Files: `~/Work/character_art_cutouts/local_matte/<Character>/`.

Consequences:
- **No art changes:** faces, poses and style stay exactly the app's art.
- **Approved motion carries over:** the cutouts sit at the same coordinates as the source
  PNGs, so the approved warp-mode configs (`configs/<char>/<expr>.json`: eye positions, blink,
  breathing mask, sway, pins) apply as-is. Only silhouette/warp zones/barriers become unnecessary.
- **Plate per expression (decision pending, recommended):** each expression's background is
  that PNG with the figure painted out (inpainted locally). Outside the figure, the plate is the
  original pixels. Frame 0 then looks the same as today's PNG and switching expression shows the
  same scenery as today. A single shared plate per character (fixes the scenery swap noted
  above) is an optional later step.

### Phases

| # | Step | Output | Gate |
|---|---|---|---|
| 0 | Cut out all 60 originals | `character_art_cutouts/local_matte/` | done, user-approved |
| 1 | Celeste pilot: 12 plates (inpaint figure area), layer folder per expression, convert the 12 approved configs to layer configs | `layers_v2/celeste/` | plate review sheet |
| 2 | Render Celeste's 12 clips in layer mode; QC: background bit-identical, PNG = frame 0; old-vs-new side-by-side video | `output_layers/celeste/` | user review |
| 3 | Swap Celeste's PNG + WebM in the app (per-replacement approval), on `experiment/ai-companion`, not pushed | app commit | user approval |
| 4 | Nova (most benefit: starfield, floor reflection as its own layer; neutral config missing, rebuild) | | user review |
| 5 | Daisy, Evelyn, then Mira (translucent slime: check the matte inside the body) | | user review |
| 6 | Optional: one shared plate per character; new characters delivered layered | | decision |

**Status 2026-11-16 morning:** phases 1, 2, 4 and 5 rendered for all 5 characters (60 clips,
background bit-identical in every frame). Celeste approved by the user on the first 5 clips;
the rest await review. Mira has the extra slime wobble (sway ×1.5, softer, more head lag, fuller
breath). Review: `reports_layers_v2/<char>/<char>_REVIEW_all12.mp4` and `<char>_plates_sheet.png`
in the pipeline. Phase 3 (app swap) not started.

**Status 2026-11-16 (later):** the user reviewed all 5 reels ("these look great") and approved
the swap. All 60 PNG + WebM pairs in `Character_Art/<Name>/` are replaced by the layer-mode
outputs; each PNG is frame 0 of its clip (checked against the lossless master). Manifest
provenance and MODELS_AND_ASSETS.md updated (the PNGs are no longer byte-identical to the
original generations). Phase 6 (shared plate) stays optional. Guidance for new characters:
[../NEW_CHARACTER_GUIDE.md](../NEW_CHARACTER_GUIDE.md).

### Problem

The current idle clips (`Character_Art/<Name>/animations/`) are made by warping one
flattened PNG. The warp mask feathers out around the body, so a band of background next
to the hair, shoulders and hips moves with the character. On busy backgrounds this reads
as the scenery wobbling. Nova is the worst (starfield, city lights, window frame), and
Daisy and Evelyn show it to a lesser degree.

A second problem was found during the review: the backgrounds are not the same across a
character's 12 expression PNGs. For Nova, Evelyn and Daisy, 72–91 % of pixels differ between
expressions, even in corners far from the figure. Each expression was generated
separately. Celeste is nearly consistent (8–16 %). `evelyn_comforting.png` (and the
native Evelyn neutral) also uses different framing from her other expressions. Because of this,
switching expression also swaps the scenery.

### Proposal

Split each character into layers and animate only the character:

| Layer | Per | Moves? |
|---|---|---|
| Background plate (clean, character removed, area behind her painted in) | character | never |
| Reflection / contact shadow (where present, e.g. Nova's floor) | expression | follows the sway |
| Character cutout with alpha (incl. hair strands) | expression | breathing, sway, blink |

The pipeline (`~/Work/edgeloop-animation-pipeline`) composites the warped cutout over the
plate each frame. Background pixels then stay bit-identical by design, and the QC gate tightens
from "far background static" to "every background pixel static". One plate per character
also makes expression switches keep the same scenery.

### Requirements on the art

1. The clean plate must have real scenery behind the figure. When she sways
   3–4 px, the revealed area must hold real content, not a smear.
2. The alpha matte must be good at hair edges against bright or busy backgrounds (stars,
   windows). A rough matte looks like a sticker. It's best produced at generation time,
   not cut out afterwards.
3. Reflections and shadows must be their own layer or be painted out of the plate. A
   baked-in reflection would stay still while the character moves.
4. All 12 cutouts of a character need the same scale and foot position, so expression
   switches don't make her jump.

### Suggested order

1. **Celeste first** as the pilot. Her backgrounds already match, so only one clean plate
   and the cutouts are needed.
2. **Nova next**, since she benefits the most (worst warping, reflection layer).
3. Evelyn and Daisy.
4. New characters (Helena, Sienna, …) should be delivered layered from the start: plate +
   transparent expression PNGs (+ optional reflection/shadow layer).

### App impact

None expected. The app keeps receiving one flattened WebM per expression, plus the PNG for
the static fallback. If the PNGs are regenerated from the layers, the PNG and video
first frame must stay identical, or the PNG→video fade will show a jump.

### Interim option (if real-gameplay testing finds it too visible)

Tighten Nova's matte and reduce her sway amplitude. That shrinks the moving
band but doesn't remove it.
