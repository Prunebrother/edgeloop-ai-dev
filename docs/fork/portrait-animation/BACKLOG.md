# Portrait animation backlog

## PA-1 Layered artwork: static background plate + moving character cutout

**Status:** backlog (raised 2026-11-12 after the first review of all 48 idle clips)
**Priority:** after real-gameplay testing of the current clips. Real use may show the
warping is less noticeable at portrait size during a session.

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
