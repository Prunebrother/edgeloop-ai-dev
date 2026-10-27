# F2.4 artwork inventory

Inspected 2026-10-28. All 31 source files are PNG by signature; the table records exact filenames, not assumed extensions. SHA-256 and byte sizes are in [the machine inventory](f24/artwork-inventory.json). No original was modified, renamed, regenerated or staged. The working tree was clean at the start: the earlier explicit artwork backup `b116631` already included the user changes. `backup/f24-pre-artwork-20261028` preserves it; F2.3 `2aae519` remains intact.

| Original filename | Detected format | Dimensions |
|---|---|---|
| `Character_Art/Daisy/Daisy collage.png` | PNG | 1024 × 1536 |
| `Character_Art/Daisy/Daisy_Chickens.png` | PNG | 1086 × 1448 |
| `Character_Art/Daisy/Daisy_Milk.png` | PNG | 1086 × 1448 |
| `Character_Art/Daisy/Daisy_working.png` | PNG | 1086 × 1448 |
| `Character_Art/Daisy/daisy_sundress.png` | PNG | 1086 × 1448 |
| `Character_Art/Daisy/daisy_tractor.png` | PNG | 1086 × 1448 |
| `Character_Art/Daisy/expressions/daisy_comforting.png` | PNG | 1024 × 1536 |
| `Character_Art/Daisy/expressions/daisy_concerned.png` | PNG | 1024 × 1536 |
| `Character_Art/Daisy/expressions/daisy_disappointed.png` | PNG | 1024 × 1536 |
| `Character_Art/Daisy/expressions/daisy_excited.png` | PNG | 1024 × 1536 |
| `Character_Art/Daisy/expressions/daisy_flirty.png` | PNG | 1024 × 1536 |
| `Character_Art/Daisy/expressions/daisy_focused.png` | PNG | 1024 × 1536 |
| `Character_Art/Daisy/expressions/daisy_happy.png` | PNG | 1024 × 1536 |
| `Character_Art/Daisy/expressions/daisy_mischievous.png` | PNG | 1024 × 1536 |
| `Character_Art/Daisy/expressions/daisy_neutral.png` | PNG | 1024 × 1536 |
| `Character_Art/Daisy/expressions/daisy_playful.png` | PNG | 1024 × 1536 |
| `Character_Art/Daisy/expressions/daisy_proud.png` | PNG | 1024 × 1536 |
| `Character_Art/Daisy/expressions/daisy_surprised.png` | PNG | 1024 × 1536 |
| `Character_Art/Evelyn/Expressions/evelyn_comforting.png` | PNG | 1086 × 1448 |
| `Character_Art/Evelyn/Expressions/evelyn_concerned.png` | PNG | 1024 × 1536 |
| `Character_Art/Evelyn/Expressions/evelyn_dissapointed.png` | PNG | 1024 × 1536 |
| `Character_Art/Evelyn/Expressions/evelyn_excited.png` | PNG | 1024 × 1536 |
| `Character_Art/Evelyn/Expressions/evelyn_flirty.png` | PNG | 1024 × 1536 |
| `Character_Art/Evelyn/Expressions/evelyn_focused.png` | PNG | 1024 × 1536 |
| `Character_Art/Evelyn/Expressions/evelyn_happy.png` | PNG | 1024 × 1536 |
| `Character_Art/Evelyn/Expressions/evelyn_mischievous.png` | PNG | 1024 × 1536 |
| `Character_Art/Evelyn/Expressions/evelyn_neutral.png` | PNG | 1122 × 1402 |
| `Character_Art/Evelyn/Expressions/evelyn_playful.png` | PNG | 1024 × 1536 |
| `Character_Art/Evelyn/Expressions/evelyn_proud.png` | PNG | 1024 × 1536 |
| `Character_Art/Evelyn/Expressions/evelyn_surprised.png` | PNG | 1024 × 1536 |
| `Character_Art/README.md` | PNG | 1086 × 1448 |

## Curated presentation references

The shared JSON manifest references seven existing expression images per character. `happy` is mapped to Cheerful and `focused` to Attentive after visual inspection. Neutral, Playful, Excited, Surprised and Concerned use matching originals. No crop/resize/format conversion or manufactured expression is used. Contain scaling is the default. Other source files remain archive material and are not publicly served by the local UI server.

| Standard expression | Existing source suffix, both characters |
|---|---|
| Neutral | `neutral.png` |
| Attentive | `focused.png` |
| Curious | Missing; neutral portrait fallback |
| Thoughtful | Missing; neutral portrait fallback |
| Amused | Missing; neutral portrait fallback |
| Cheerful | `happy.png` |
| Playful | `playful.png` |
| Excited | `excited.png` |
| Surprised | `surprised.png` |
| Serious | Missing; neutral portrait fallback |
| Concerned | `concerned.png` |
| Relaxed | Missing; neutral portrait fallback |

**Missing dedicated artwork, both Evelyn and Daisy:** Curious, Thoughtful, Amused, Serious and Relaxed. All twelve state IDs work; these five have no dedicated images and visibly report neutral fallback. Neutral image failure falls through to the generic placeholder. Existing `comforting`, `flirty`, `proud`, `mischievous` and `disappointed` files are preserved, not relabelled as unverified substitutes. Evelyn’s `dissapointed` spelling and the PNG named `Character_Art/README.md` are preserved verbatim.

## Provenance and redistribution

These are existing user-provided local originals, previously backed up on explicit request. Some carry embedded C2PA/AI-generation metadata; that is not a licensing grant or proof of ownership. No external art was fetched. This task does not establish redistribution rights. No new image assets or artwork-containing screenshots are committed or published by F2.4. The application references the existing files locally. Screenshots are kept in the private/local recovery directory listed in the validation report; only their hashes and dimensions are committed. Confirm rights before any future public release, and retain original provenance.
