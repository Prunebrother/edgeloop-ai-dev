# Dialogue-context A/B protocol (before sampling)

Working baseline: `7fee97c`. Personal deck SHA-256: `39e04b7cc5362b3c83ca56b9d6c06d9a24a74da79bf07326003cf46eba95c1cb`.

Freeze the 96 initial provider requests from `character-cards-v050-validation/real-character-cards.json` (source SHA-256 `f9eceb3f4440804bbcf4e69e8d8956eaf72d459a67e6a179f7f3950fdaca9ec5`). They cover all 48 cards, two synthetic active-session scenarios and four installed F29 models. Use initial requests, not response-dependent fidelity correction retries. This is a prompt-replay investigation, not a replacement production delivery benchmark.

A is the captured production request. B moves only the historical prefix preceding the expression reminder/current card instruction into one ephemeral assistant-role context message. The existing background/provenance labels and all historical words remain. No history is promoted to system authority. Any explicitly labelled standing user instruction remains in the current user-role message. Current task, personal brief, native system identity, facts and all other instruction bytes remain unchanged. For the frozen main cases, concatenated message content must be byte-identical. No production compiler change is enabled.

There are 56 raw-answered-history cases, 36 selected-story-context cases and four no-history negative controls. No prefix is removed in the controls, so their A/B requests must be identical.

Run seeds 271828 and 314159 on every case, paired between variants: **384 initial generations**. Both arms receive the same seed option; every original sampling parameter stays fixed. Alternate AB/BA order by case and seed; group by model to avoid unnecessary reloads. Capture exact request hashes, output, stop reason and provider metrics. No early stopping or parameter tuning based on results. Only existing local port 11435 is permitted; no tools, model creation/pulls, Modelfile edits, hardware or production session controls.

Primary objective metric is literal prior-message marker occurrence, using the same narrow boat/café marker lists as the original harness. It is an indicator, not a semantic classifier, and performs no output filtering. Report by seed, model and context route, with paired discordance counts. The four unchanged-prompt controls test repeatability under the same seed. Treat observations as clustered by model/card/scenario, not independent user-level trials; do not claim population significance from a naive pooled test.

For seed 271828, review every A/B output (192) against the unchanged brief and supplied evidence using shuffled blind IDs with the arm key stored separately. This is a single assistant analyst's rubric-based review, not independent human adjudication or an inter-rater reliability estimate:

- **Semantic stale echo:** reanswers, continues or imports irrelevant details from the answered boat/café request. Incidental common vocabulary alone is insufficient.
- **Invented history:** unsupported past shared events, new autobiographical episodes, or completed actions presented as established history. Native canon, the actual earlier answered exchange, explicitly hypothetical scenes and wishes are allowed.
- **Unsupported inference:** asserted current participant feeling, bodily state, disposition/performance, fabricated perception or scientific conclusion not supported by the synthetic facts. Explicit guesses, optional questions and conditional/fictional premises are not automatically violations.
- **Card adherence:** 0 = wrong/mainly unrelated intent; 1 = intended topic partly realized but a material brief constraint or focus is broken; 2 = intended action and material constraints satisfied. A topical response can still fail factual or no-question constraints.

Record all annotations, including ambiguous cases, before revealing arm labels. Report subjective results separately from literal marker counts. Seed 314159 is the predefined replication for the objective metric; it is not a second fully annotated quality sample.

Preserve all personal briefs, production modules, model storage and hardware protections. Recommend a small fix only if supported by results; no architectural change is implemented without review.
