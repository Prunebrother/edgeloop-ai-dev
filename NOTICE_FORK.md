# Attribution and corresponding source

This fork contains EdgeLoop by marshallmims, version 1.1.3, commit
`d351e011249079b368ebdc8d46f83b260be7d2a5`:
https://github.com/marshallmims/edgeloop

The original LICENSE and upstream notices remain intact. The original engine,
physiological calculations, session rules, calibration and hardware drivers
remain authoritative. The immutable upstream pin and reviewed integration
changes are recorded in `docs/fork/upstream-pin.json` and `f2-changes.json`.

F2.2 includes adapted AGPL-3.0-only AI conversation/provider/Director/storage
source from the local EdgeLoop AI project, committed baseline `9e89fa1`, plus
selected character-development working files. Corresponding migrated source
is included in this repository under `companion_ai/`, `characters/` and
`tools/characters/`. Exact source paths/hashes and adaptations are recorded in
`docs/fork/f22/migration-sources.json`. The legacy repository is preserved and
is no longer required at runtime. No legacy session coordinator, hardware
controller, control executor, voice service or redundant dashboard is included.

Distribute this corresponding source, the LICENSE and attribution with fork
changes as required by AGPL-3.0-only, including when made available over a
network. User conversations, credentials, model weights, private data and
virtual environments are not part of this source checkout. Character source
Modelfile bytes are preserved; existing installed models/weights were not
copied, recreated or deleted by consolidation.
