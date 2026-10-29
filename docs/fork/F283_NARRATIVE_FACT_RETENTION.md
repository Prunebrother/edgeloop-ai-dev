# F2.8.3 — Reliable narrative memory

Starting HEAD `7c190fa`, clean `experiment/ai-companion`. The post-F2.8.2 free-form objective change is preserved. Comparison baseline is `ff0f1ba` (`f2.8.2-checkpoint`).

## Reproduced findings before implementation

- A standalone user statement, `The truth was hidden in plain sight.`, is not retained unless it also matches a premise/choice invitation rule. Legacy extraction stores selected user choices/premises and assistant excerpts, not all established user details.
- With both reported details explicitly present in Story Memory, the baseline compiler selects unrelated `threads:0` and `commitments:0` for both `What did the page say?` and `What do you collect?`. Neither target detail appears in outgoing context. The queries do not lexically match the quotation or the noun “collection”; category priority and the soft budget favor other excerpts. [Synthetic trace](f283/root-cause.json).
- Legacy excerpts carry no speaker, epoch or semantic category per item. Contradictory assistant developments can coexist and outrank older details. Important developments also share the same short rolling retention queue as incidental prose.
- Normal backend reset clears developments and changes epoch in the reproduced baseline. The UI accepts same-model state messages without checking epoch/revision. An out-of-order/stale snapshot can therefore repopulate its display; this is a testable weakness, not a proven account of the user's run. The available local persisted record contains neither reported detail or a per-request trace. No private transcript was printed or changed.

Implementation, regression and evaluation results follow in subsequent checkpoints.

## Implementation and lifecycle

Implementation commits: `14984df8c8a32c31b5d574e6d2ebeb9655cb14d3` (memory/compiler/diagnostics) and `99e08b86b169f6814c415cf4a7af3312805064a7` (bounded UI epoch fencing). Final tag: **`f2.8.3-checkpoint`**; its exact documentation/evidence commit is `git rev-parse 'f2.8.3-checkpoint^{commit}'`.

Existing NarrativeMemory now owns up to **16** attributed records, with original wording/value (up to 320 characters), source speaker, category, scope, epoch, status and extraction cue. Categories distinguish user facts, character details, hypotheses, developments and commitments. No additional store, model, vector index or inference call was added. User facts are captured when an authenticated turn is accepted, even if generation is later cancelled. Incidental developments are evicted before precise clues/preferences. Overlong precise quotations are not silently clipped into “exact” facts.

Slot rules cover quotations, collections, explicit preferences, named story roles and relationships. An assistant contradiction becomes a conflicting record and does not overwrite an active established slot or enter legacy developments. Explicit user corrections supersede dialogue details. The selected model's existing SYSTEM remains immutable canon; explicit named relationships are additionally derived from that text for conflict checks (including Celeste/Laurent), not invented in a competing persona definition. Legacy records migrate with **unknown** speaker attribution rather than guessed provenance. Persistence remains opt-in in the existing file, and migration does not rewrite the user's files during development.

Recall intent and matching facts now outrank unrelated threads/summaries. Selection uses source/category and narrow linguistic cues, including collect/collection aliases and page/quotation context. Selected records keep precise wording and provenance. Explicit instructions distinguish prior evidence from new fiction, tentative hypotheses, and unavailable evidence. Missing/budget-excluded evidence requests uncertainty rather than invented dialogue. F2.8.2's hard limit, revision transport, current-message preservation, category caps and recent-dialogue allocation remain. Recall may reserve up to two compact matching items; it does not raise every soft target or dump all facts into prompts. Conflicting assistant history is excluded from inference while the transcript remains intact.

Filtering now targets actual operational assertions rather than banning all numbers or words such as “heart” and “session.” Fictional chapter numbers and literary usage survive; measured BPM, actual sensor connectivity and running-counter assertions stay outside story facts. These rules do not make narrative text authoritative telemetry. Free-form fictional objectives remain free-form; no Modelfile, preset, artwork, engine, driver or hardware pathway changed.

The baseline normal reset cleared memory correctly; no historical per-request trace proves why the reported drawer stayed populated. This milestone hardens two reproducible paths: failed reset persistence now leaves the old epoch intact and reports failure, and the UI rejects stale sequence/revision snapshots and retired epochs. A monotonic per-model sequence continues to fence snapshots even after the bounded retired-epoch list evicts an old ID. Reconnection resets the presentation gate for a new backend process. Reset retains transcript history, clears active story records, and prevents persisted abandoned facts returning. Objective abandon/reset, model switching and opt-in session restoration use the same scope/epoch rules.

## Diagnostics

Story Memory displays the active epoch and each bounded record's category, speaker, status, wording and whether the last applicable prompt selected it. Context Intelligence reports recall intent/evidence, selected IDs, epoch and exclusions (`irrelevant`, `budget`, inactive/conflicting, wrong scope/epoch or native-canon conflict). Legacy attribution and tentative evidence are labelled explicitly. The UI uses text nodes and adds no transcript dump or new control pathway. Diagnostics for an earlier epoch are not presented as current selections.

## Matched results and regression

[Evaluation](f283/evaluation.json), [validation](f283/validation.json), [upstream](f283/upstream-tests.json), [browser attempts](f283/browser-results.json).

The harness loads the actual `ff0f1ba` NarrativeMemory and compiler from Git, then compares identical synthetic conversations across Evelyn v1, Daisy v1 and Celeste v2. It covers stored-but-unselected details, a forty-turn detour, contradictory assistant recalls and missing evidence, with thirty compilation repetitions. Native-source SYSTEM lengths are used for offline budgeting; installed metadata was not accessible.

- Expected evidence reaches outgoing context in **18/18** F2.8.3 cases versus **0/18** F2.8.2 cases. All six missing-evidence cases receive explicit uncertainty guidance. This is **evidence retrieval coverage, not generated-answer accuracy**.
- For stored clues, estimated quotation prompts change from 2,792 → 3,068 (Evelyn), 2,838 → 3,114 (Daisy), and 4,176 → 4,452 (Celeste). Collection prompts change from 2,791 → 3,077, 2,837 → 3,122, and 4,175 → 4,461. These are conservative character/UTF-8 estimates, not provider tokenizer counts. Added recall rules/source evidence cost approximately 276–286 estimated tokens in this fixture, with the same hard context/output allowance.
- The median of per-case compilation medians is **0.5472 → 0.6099 ms**, including identical fixture copying in both arms. This local CPU sample is not a provider-latency result.
- **1,057 upstream tests, 504 Python tests and 42 companion JavaScript tests pass.** There are 35 new Python cases and five UI snapshot-gate tests. Python covers exact quotation/collection recall after 48 detours, conflicts, corrections, missing/tentative evidence, legacy migration, persistence/reset failure, epochs, model isolation, numbers versus actual telemetry, budget exclusions, cancellation and native SYSTEM/expression compatibility.
- The unfiltered Python run has the same three environment failures: occupied observer port, occupied UI port and desktop HTTP pairing. They are deselected in the final run because socket creation is denied with `EPERM`. In-process TestClient scheduling uses the previously documented `/tmp`-only 20 ms selector shim; production is unchanged. One existing Starlette deprecation warning remains.
- All seven browser workflows were attempted on isolated fixture ports and failed before acceptance due to socket/Chromium restrictions. The extended Context Intelligence workflow checks the original quote in outgoing context, fact/source display and reset clearing while retaining transcript, but no browser/layout pass or screenshot is claimed.
- Existing Ollama discovery at `http://127.0.0.1:11435` is inaccessible (`ConnectError`). **Zero live generations** occurred. The comparison harness supports sequential synthetic Evelyn/Daisy/Celeste evaluations, actual provider prompt/latency metrics and exact-substring scoring when available, always `think: false`. No prior live result substitutes for this milestone.

## Limits and activation

Extraction and corrections use bounded English patterns, not semantic understanding. Implicit references, arbitrary rephrasings, ambiguous objects and canon conflicts outside supported explicit relationship patterns can still be missed. Native canon instructions remain the general boundary. Record/field limits and hard/category budgets can exclude evidence; diagnostics expose selection decisions. Legacy provenance may be unavailable. The legacy compiler fallback does not gain the full recall-aware selection policy.

Supplying the correct evidence does not guarantee the model uses it. Conflicting generated prose is quarantined from active memory/history selection; this is not a new post-generation dialogue rewrite or an extra LLM correction call. User streaming remains provisional under existing validation. Actual provider tokens, latency, VRAM, live recall accuracy and subjective narrative quality remain unmeasured here. No comprehensive physical-hardware validation is claimed.

Reproduce without hardware:

```sh
.venv/bin/python -m pytest -q tests/ai tests/fork
node --test --test-isolation=none --test-reporter=tap tests/fork/*.test.mjs
.venv/bin/python tools/fork_validate.py --tests --report /tmp/f283-upstream.json
.venv/bin/python -m tests.fork.narrative_fact_evaluation --output /tmp/f283-evaluation.json
# Optional sequential calls to the existing Ollama endpoint only:
.venv/bin/python -m tests.fork.narrative_fact_evaluation --live --output /tmp/f283-live.json
CONTEXT_BROWSER_REPORT=/tmp/f283-context node tests/fork/context-intelligence-browser.mjs
```

No services were restarted, installed models rebuilt, or private conversations edited. At a suitable session boundary, preserve wanted nonpersistent conversation before manually restarting only the observer and reloading the UI:

```sh
systemctl --user restart edgeloop-ai-observer.service
```

Saved legacy memory can migrate; unpersisted details in another running process cannot be reconstructed from missing logs. The existing web/Ollama services can stay running. No new configuration or sampling preset is required.
