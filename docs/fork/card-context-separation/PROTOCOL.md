# Implementation validation protocol

Baseline `07f9d5d`; production change limited to `ContextCompiler.compile.assemble` on deck-card turns. No card text, model storage, scheduling or controls changed.

Reconstruct the 96 frozen synthetic cases using recorded prior/card replies and the real ConversationService. Compile each initial request with the baseline compiler loaded from a local file and the implemented compiler using the exact same inputs. Require baseline wire requests to match the original capture byte-for-byte, and implemented requests to equal the previous A/B intervention. Non-card setup compilation must be unchanged. No hardware or real inference is used during capture; only local `/api/show` metadata reads.

Repeat the previous two-seed (271828, 314159), four-model experiment: 384 new initial generations on port 11435, with the unchanged options/order/scenarios. Variant B must use captured implemented requests directly. No result-dependent tuning or early stopping. Check exact request/output reproducibility against the earlier experiment, as well as all negative controls.

Use the original metric definitions. Literal marker counts cover both seeds. Semantic echo, invented history, unsupported inference and adherence use the 192 first-seed outputs, matching the previous review scope. If a displayed output is byte-identical to the earlier reviewed output for the same case/arm/seed, reuse its frozen annotation and disclose this. Review any changed first-seed output against its brief/evidence before assigning its arm. Do not claim fresh independent blinded review for reused ratings. Second-seed quality is not manually scored. Report dimensions separately, including any lack of improvement.

Run focused compiler, narrative, Director, card and lifecycle regressions; exercise standing directives, missing assistant replies, real user/non-card paths, prompt budget and transcript integrity. Record remaining grounding issues without rewriting personal briefs. Preserve a local checkpoint and stop for review, with no development merge, push or publication.
