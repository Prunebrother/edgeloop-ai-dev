# F2.8.4.2 — Source-backed, significance-aware memory

Investigation baseline: `710b81e` on `experiment/ai-companion`. The working tree already contained browser-runner changes; those and the user's character directories were preserved. This is a deterministic memory repair, not a hobby-specific policy or a new memory service.

## Evidence and root causes

The supplied `/tmp/memory-full/report.json` has three semantic hobby successes in A and none in B/C. Original strict hobby scores are A **1/3**, B **0/3**, C **0/3**. All six failed B/C hobby answers have no selected fact IDs. The saved report lacks the original establishment replies and intermediate memory snapshots, so it cannot retrospectively distinguish extraction failure from eviction for each live response. An empty selected-ID list alone does not prove budget exclusion.

Frozen-checkpoint replays establish two independent defects:

1. Natural source statements were stored under sentence-derived generic keys. Closed recall-slot matching and literal word matching missed them, including before any detour or budget pressure. The compiler deliberately excluded generic summaries for several recall intents, removing the fallback source.
2. Retention prioritized slot shape and recency over meaning. Generic autobiographical details, agreements, discoveries and user-established propositions could lose to routine detours. Source wording was part of generic slot identity, so differently worded updates could also become separate records rather than supersede one relation.

In the expanded matched replay, the checkpoint stores all 39 original source statements. Immediately afterward, 21/39 receive selected structured evidence (30/39 appear verbatim somewhere in the prompt). After 40 detours, only three original records remain, and none of the 39 original statements reaches the prompt. The retained three are unmatched, not excluded by budget. These are synthetic causal reproductions, not recovered B/C establishment transcripts.

## Repair

`companion_ai/fact_semantics.py` provides bounded grammatical subject/relation descriptors, morphology and relation-type concepts. It does not enumerate permitted professions, story objects, character hobbies or fictional values. The existing extractor, merge/retention function and retriever use the same descriptors:

- Arbitrary possessive attributes, preferences, boundaries, roles, origins, residences, named relationships, interests, commitments, discoveries and subject/property propositions receive meaningful keys. Exact quotations and identifiers keep their existing handling. Unsupported syntax still has the existing excerpt fallback.
- Source text, source speaker, source type, model identity, epoch and record ID are retained. Property values come from source spans, not generated summaries. Legacy retained details can be reclassified from their original source without reconstructing missing history.
- Significance separates explicit user corrections, precise clues, stable personal/relational facts and substantive commitments from hypotheses, temporary states, instructions and routine meta replies. Storage remains **16 facts**; ties expire oldest first. There is no permanent-record flag or context-limit increase.
- Relation keys allow explicit user corrections and temporal updates to supersede prior values. Assistant replacements remain conflicts. Equivalent rephrasings retain the original source. Negation is preserved, and explicit corrections changing specificity do not disappear as duplicates. Multiple interests can coexist. Ambiguous unscoped corrections are diagnosed instead of overwriting several facts.
- Retrieval combines source-word overlap, relation concepts, significance and correction precedence. A prompt cue can help rank a matching fact but cannot alone establish relevance for ordinary attributed facts. Participant versus character ownership, model and epoch boundaries remain enforced; third-party quotations do not establish the character's autobiography.
- Unsupported historical recall answers cannot seed invented prior facts. Explicit invitations to introduce new fiction remain distinct. Existing native relationship-canon checks remain in place; this does not attempt to infer every immutable native biography fact automatically.

The Context Compiler exposes significance and semantic tags with selected/irrelevant/budget decisions. Foreign-model and old-epoch diagnostics omit semantic contents. Existing allocation, history reservation, factual grounding, expression handling and revision paths remain intact. Manually configured objectives still use their existing lifecycle and compiler path. Session Journal stays separate.

## Bounded diagnostics and scoring

The browser runner saves snapshots after establishment, after detours and at recall, including at most 16 source records, eight storage decisions, extraction replay candidates, scope/epoch, matched/selected IDs and budget decisions. Establishment source capture is limited to 4,096 characters and records truncation. Recall snapshots use pre-answer storage with that answer's actual compiler diagnostics, so an invented reply cannot count as its own evidence.

Outcomes distinguish absent establishment, missed extraction, eviction, unmatched evidence, budget exclusion and other context exclusion. Source errors/truncation remain visible. The fixture replays the actual arm's extractor for diagnostics; it does not make another inference call or persist proposed facts.

Original strict answer and success predicates remain unchanged. Separate lexical semantic coverage handles paraphrases and case-insensitive identifiers. Supplemental unsupported-addition checks flag replacement identifiers, incomplete/replacement fact answers and extra explicit personal pursuits for review. Free-text coverage rejects detected denials and uncertainty. These are transparent heuristics, not an entailment judge; they cannot certify every extra biographical assertion, negation scope or metaphor. Source snapshots support human review.

`--deterministic-only` runs A/B and verifies curation is off when setup succeeds. Default A/B/C availability remains intact, but **C was not run during this investigation**. No inference calls, resident models, embeddings or cloud dependencies were added to production memory handling.

## Measured validation

The CPU comparison uses the same source statements, native-persona reservation, history fixtures and 40 detours in both versions: 12 diverse fact scenarios for each of Evelyn/Daisy/Celeste, plus the three original activity examples. It includes paraphrased questions and 30 applicable explicit corrections.

| Measurement | Checkpoint B | Fixed B |
| --- | ---: | ---: |
| Structured evidence selected after establishment | 21/39 | 39/39 |
| Original source retained after detours | 3/39 | 39/39 |
| Structured evidence selected after detours | 0/39 | 39/39 |
| Original wording present in prompt after detours | 0/39 | 39/39 |
| Corrected evidence selected | 15/30 | 30/30 |

The three activity regression cases are included, not privileged by this scoring. All three select their established evidence after detours in fixed B. This establishes retrieval/context correctness, **not live generated-answer accuracy**.

Prompt estimates use the existing compiler heuristic, not an Ollama tokenizer. Median prompt size after detours is about **3,102 → 3,156 estimated tokens**, with unchanged hard limits. Median compilation time in the final run is **0.86 → 2.67 ms**; timings vary with host load. Compact results are saved in [f2842-memory-evaluation.json](f2842-memory-evaluation.json). Matched greetings have byte-identical outgoing messages in all three characters, with unchanged estimates (Evelyn 2,776; Daisy 2,764; Celeste 4,102). No static prompt instructions were added.

Regression results:

- **658 Python tests pass**, three socket-dependent tests excluded from that run. Running those three separately produces two failures and one setup error at socket creation (`PermissionError: [Errno 1] Operation not permitted`). A test-process-only selector polling shim was used for in-process asynchronous tests because this managed environment also denies asyncio self-pipe writes; production code was not changed for it.
- **61 companion JavaScript tests pass**.
- **1,057 upstream tests pass**; the original engine file verification passes.
- Tests cover long detours, diverse facts, contradictions, specificity/polarity changes, commitment-date updates, missing evidence, native relationship protection, multiple interests, participant ownership, third-party reports, persistence, privacy disablement, reset, character isolation, budget exclusion and expression compatibility.

The real A/B browser run was attempted with curation disabled. It stops at Ollama preflight with `connect EPERM 127.0.0.1:11435`. Neither character setup nor any new real-model conversation ran. No provider-token or inference-latency measurement is available. Browser/socket acceptance remains environment-blocked; live recall acceptance is **pending**. No running observer/Ollama service was restarted or stopped.

## Reproduce

From the repository, use:

```sh
.venv/bin/python -m tests.fork.significant_fact_evaluation --output /tmp/f2842-replay.json
.venv/bin/python -m pytest -q tests/ai/test_significant_facts.py tests/ai/test_hobby_recall.py
node --test --test-isolation=none tests/fork/*.test.mjs
MEMORY_REPORT=/tmp/f2842-live-ab node tests/fork/intelligent-memory-browser.mjs --live --deterministic-only
```

Current artifacts: `/tmp/f2842-replay-final.json`, `/tmp/f2842-python-final.log`, `/tmp/f2842-js-full.log`, `/tmp/hobby-upstream.json`, and `/tmp/f2842-live-ab/report.json`. The original `/tmp/memory-full/` evidence was not overwritten. The browser command uses isolated, test-owned storage/processes and retains the existing scenarios and strict scores.

## Limits

This is a transparent English grammatical/lexical system, not universal semantic understanding. Unrecognized syntax, aliases and indirect references can still miss retrieval or update alignment. Ambiguous corrections require a clearer target. A full set of equally significant facts can still evict an older fact; evicted information cannot be reconstructed from nothing. Curation remains optional and default-off. Actual answer accuracy, unsupported additions and personality continuity require the blocked real-model comparison before claiming F2.8.4.2 live acceptance. Native personas, sampling settings, artwork, installed models, hardware pathways, safety logic and user data were not changed.
