# F2.8.3 — Reliable narrative memory

Starting HEAD `7c190fa`, clean `experiment/ai-companion`. The post-F2.8.2 free-form objective change is preserved. Comparison baseline is `ff0f1ba` (`f2.8.2-checkpoint`).

## Reproduced findings before implementation

- A standalone user statement, `The truth was hidden in plain sight.`, is not retained unless it also matches a premise/choice invitation rule. Legacy extraction stores selected user choices/premises and assistant excerpts, not all established user details.
- With both reported details explicitly present in Story Memory, the baseline compiler selects unrelated `threads:0` and `commitments:0` for both `What did the page say?` and `What do you collect?`. Neither target detail appears in outgoing context. The queries do not lexically match the quotation or the noun “collection”; category priority and the soft budget favor other excerpts. [Synthetic trace](f283/root-cause.json).
- Legacy excerpts carry no speaker, epoch or semantic category per item. Contradictory assistant developments can coexist and outrank older details. Important developments also share the same short rolling retention queue as incidental prose.
- Normal backend reset clears developments and changes epoch in the reproduced baseline. The UI accepts same-model state messages without checking epoch/revision. An out-of-order/stale snapshot can therefore repopulate its display; this is a testable weakness, not a proven account of the user's run. The available local persisted record contains neither reported detail or a per-request trace. No private transcript was printed or changed.

Implementation, regression and evaluation results follow in subsequent checkpoints.
