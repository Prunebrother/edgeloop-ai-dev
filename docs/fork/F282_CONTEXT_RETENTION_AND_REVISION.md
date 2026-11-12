# F2.8.2 — Context retention and revision reliability

## Scope and checkpoint

Started from clean `1ac5091` on `experiment/ai-companion`; no user changes were present. Implementation commit: **`5a85202fe13fb5e67ea6f13cf531be79e283fc7f`**. Final checkpoint tag: **`f2.8.2-checkpoint`**; resolve its documentation/evidence commit with `git rev-parse 'f2.8.2-checkpoint^{commit}'`.

This changes the existing compiler/allocation and revision path, plus compact diagnostic fields. It adds no narrative engine, model, controller, inference daemon, automatic objective or extra inference/retry allowance. No active service was restarted. Original engine, hardware pathways, safety behavior, character Modelfiles, artwork, installed models, sampling presets and private conversation/settings data were preserved. The only upstream-pinned file changed for this milestone is the service-worker cache version for updated diagnostics.

## Reproduced failures

The matched harness loads the **actual F2.8.1 compiler from Git**, not a reimplementation, and supplies identical synthetic state/history/memory and local character SYSTEM text to both compiler versions. The fixture is authenticated-observer-shaped data, not a physical session or retained user conversation.

At the default 2,800 soft target, native SYSTEM plus mandatory prompt content consumed the soft allowance for Evelyn v1, Daisy v1 and Celeste v2. F2.8.1 preserved mandatory content by exceeding the target, but then allocated zero optional history/story context in the matched ordinary-turn cases. This was soft-budget starvation, not exhaustion of the 8,192 hard context.

Repetition retries passed a prose revision request while retaining the event trigger. The compiler replaced the revision request/draft with its generic event-response sentence. Ordinary user retries retained the prose but were classified `context_only`, requesting generic silence. Both defects reproduce without inference.

## Allocation repair

The configured soft target remains **2,800**, with the same history/story category allowances, native identity reserve, output reserve and hard context limit. Allocation now:

1. Preserves the current input, essential grounding, relevant authoritative facts and applicable explicit historical user directives. Mandatory data that cannot fit produces `ContextBudgetError`; it is not truncated.
2. Filters and ranks history/story with the existing relevance, model/session/epoch and abandonment rules.
3. Gives a protected opportunity to the newest eligible dialogue message, one highest-ranked relevant nonduplicate story item, then the preceding eligible dialogue message. Whole items must fit their category allowance and remaining hard capacity. This alternation prevents history from consuming all story capacity.
4. Extends the **effective soft target only to the actual selected retention set**, when needed. This is not an unconditional increase to 5,000 or a larger model context.
5. Uses the remaining soft allowance for ranked extras, removes duplicate excerpts, and checks the cost of the assembled messages including narrative-container/message framing. Optional items are shed under hard pressure; insufficient mandatory capacity fails explicitly.

The protected set is up to two eligible recent messages and one relevant story item, not a promise to fit arbitrary long text. Disabled memory, zero category allowances, duplicate excerpts, topic changes, epoch boundaries and insufficient hard space can reduce it. Explicit directives retain their previous priority over optional category allowances. Retained messages are emitted in chronological order and stored history/memory is not changed by compilation.

Context Intelligence shows retained dialogue/story counts, effective target and soft-target extension. Diagnostics explain whether the target was extended and which items were omitted. Normal model/conversation isolation, narrative reset and manual objective lifecycle remain intact.

## Explicit revision path

The Director now passes an internal structured `revision` record with original source (`user`/`event`), original request and candidate draft. This is not a new public command endpoint. The compiler validates the record and selects `revise_reply` attention using the **original request/event topic**.

The final transport turn contains a repair instruction and the complete serialized original request/draft, clearly marked as untrusted revision data. It is never replaced by generic event text or classified as a new event/silence opportunity. Relevant current facts, the original validated event and completed-session evidence remain available. The F2.7 fallback also preserves the structured repair content and original source.

Candidate drafts are excluded from factual evidence of what the user reported. For user revisions, factual checking receives the original user request; event revisions do not promote application/draft text to a user report. A regression proves an invented posture in a draft cannot validate itself as user testimony.

The existing streaming/reset callbacks, expression envelope, generation/session/model/epoch cancellation checks, bounded retry timeout and final grounding validation remain. A failed repetition repair can fall back to the **already validated original draft** on a user turn, as before; it cannot save the rejected fabricated hardware claim. Repetitive event fallback remains suppressible. Oversized complete repair input fails the context limit rather than silently clipping the original request or candidate. No new inference call or increased retry allowance was introduced.

## Telemetry relevance

An ordinary greeting/story/goodbye now receives compact session status, identity and freshness, together with the unchanged grounding SYSTEM. It does not automatically receive every device connection, readiness, numerical measurement, source footer or channel/motion explanation.

Direct physiology questions include measurement/source/trend evidence. Device questions include device readiness, connectivity and motion availability. Settings/timing/milestone queries and triggering events retain the corresponding authoritative fields. Current protective conditions and critical events preserve protective-state data and relevant availability/device facts even on an ordinary greeting. The factual guard still receives the **full canonical contract** independently of prompt selection. Stale/unknown readings are not turned into measurements, and simulation is not physical telemetry.

The generic grounding and expression instruction constants were not shortened or rewritten in this milestone: broader redundancy changes were explicitly deferred. The ordinary-data renderer can omit its redundant hardware-boundary footer because the unchanged SYSTEM already establishes those boundaries; fallback/default renderer behavior remains available.

## Matched measurements

Evidence: [context-benchmark.json](f282/context-benchmark.json). There are seven cases per character per arm, thirty compilation repetitions each: greeting, longer recent dialogue, callback, direct telemetry, verified completion with pre-reset retained summary, ordinary revision and event revision. Source Modelfiles provide native identity lengths; these are not a claim about installed live metadata.

All token figures below are the repository's **conservative UTF-8/character estimates**, not measured provider tokens. Default model context is 8,192 with 2,048 reserved output tokens in the offline comparison.

| Character | Greeting F2.8.1 → F2.8.2 | Longer dialogue F2.8.1 → F2.8.2 | Greeting/dialogue history and story retention |
|---|---:|---:|---|
| Evelyn narrative v1 | 2,909 → 2,794 | 2,919 → 3,283 | 0 messages/0 items → 2 messages/1 item |
| Daisy narrative v1 | 2,954 → 2,839 | 2,964 → 3,328 | 0/0 → 2/1 |
| Celeste narrative v2 | 4,292 → 4,177 | 4,302 → 4,666 | 0/0 → 2/1 |

Greeting estimates fall by 115 while retaining context. Longer dialogue estimates increase by 364 because the full recent messages are now retained; this is the intended retention cost, not an unexplained regression. No fixed 5,000 target was applied. Cases without relevant story content do not invent it merely to fill a reservation.

Completion estimates decrease by 141 in this fixture while retaining two recent messages and the verified pre-reset summary. Event-revision estimates increase by 94: the draft/request that F2.8.1 discarded are now carried, alongside recent dialogue. Ordinary revisions select `revise_reply` rather than `context_only`. These are transport/selection results, not proof that actual model responses are more natural.

The median of per-case compilation medians was approximately **0.42 ms before / 0.51 ms after** in the archived run. The harness includes identical fixture copying in both timings. This small CPU increase comes from checking whole assembled optional selections. It is a local sample, not a guaranteed latency result. Actual provider prompt tokens, first-token latency, response time and GPU usage could not be measured because localhost sockets are denied here. No inference or subjective narrative improvement is claimed from this run.

## Separate investigations — intentionally unchanged

**Broad memory filtering:** `NarrativeMemory.excerpt` still removes sentences containing any digit or broad operational keywords. A benign “We will meet at the garden tomorrow” survives; “We will meet at the garden at 7” and “Our fictional session is a journal chapter” do not. The existing user-plan exception is narrower than general excerpt extraction, and compiler history filtering can remove an entire operational-keyword turn. These may harm useful continuity, but changing extraction semantics is broader than fixing allocation. Recommendation: separately review provenance-aware filtering with positive/negative examples; no filtering policy was changed here.

**Sampling overrides:** outgoing runtime options explicitly override Modelfile defaults. Runtime defaults are temperature 0.4/top-p 0.95, compared with source Evelyn/Daisy temperature 0.6 and Celeste temperature 0.7/top-p 0.9. Saved model presets can differ; this does not establish what the running user process selected. Recommendation: review per-model sampling policy separately and benchmark it. No preset or Modelfile was edited.

> **Resolved 2026-11-12:** sampling now belongs to each Modelfile. The app sends no temperature, top_p, top_k or repeat_penalty unless code sets one on purpose (e.g. a temperature-0 evaluation). Sampling values in saved `selection.json` / `model-presets.json` are ignored. Benchmark: a live Mira comparison (app 0.4 vs Modelfile 0.7, 2 runs each) showed 29 → 7 repeated five-word phrases and fewer unsupported claims, with no regression in deck behaviour.

**Redundant grounding:** the unchanged generic grounding plus expression SYSTEM adds 2,484 characters, estimated at 994 tokens by the conservative estimator. Native character boundaries and timing/history footers overlap with some of these rules. Targeted ordinary-telemetry selection already frees useful space. Recommendation: consider later matched wording reductions while retaining provenance, unknown-source, read-only authority and simulation boundaries. No broad static-instruction rewrite was made.

## Regression and unavailable acceptance

[Validation summary](f282/validation.json), [upstream report](f282/upstream-tests.json), [browser attempts](f282/browser-results.json).

- **1,057 upstream tests pass**, zero failed files, using the repository's per-file runner.
- **464 Python tests pass**, including 46 new F2.8.2 cases. Three socket-dependent tests are deselected in the final run after the full unfiltered attempt reproduced `EPERM` failures: occupied observer port, occupied web port, desktop same-origin HTTP pairing. No pass is claimed for those cases. One existing Starlette TestClient deprecation warning remains.
- **37 companion JavaScript tests pass.** Syntax checks pass for the changed UI/browser fixture. The service-worker reviewed-change manifest verifies.
- **Seven browser workflows were attempted sequentially** using isolated fixture ports, including overriding the dashboard's usual live ports. Chromium IPC or fixture socket creation failed in the sandbox; none reached acceptance. Browser layout/portraits/streaming/model-switching are **unavailable**, not passed. The Context Intelligence workflow now additionally checks retention, lack of irrelevant BLE detail and Celeste isolation, using real native-source lengths with mocked inference.
- Existing Ollama discovery at **127.0.0.1:11435** failed with `ConnectError` under the same socket restrictions. There were **zero live generations**. The benchmark supports limited sequential live comparisons for Evelyn v1, Daisy v1 and Celeste v2, with native metadata and actual provider metrics when accessible, always `think: false`. Prior archived live results are not substituted for this milestone.
- No physical hardware test, service restart, model build/unload, model size increase or new resident inference process occurred. Original EdgeLoop protective behavior is not re-certified by these software tests.

The sandbox also denies asyncio's Unix wake-socket writes. In-process Python tests used the F2.8.1 archived test-only selector shim copied to `/tmp/f282-python/sitecustomize.py`, capping selector waits at 20 ms. It is not loaded by production. It permits in-process TestClient scheduling, not TCP access.

Remaining limitations: conservative token estimates can still reject useful context early; hard/category limits can prevent whole-item retention; broad English keyword filters remain; user-streamed drafts can precede final correction; live-model prose quality, actual provider cost/latency and browser acceptance await a socket-capable environment. Two retained messages are useful minimum context, not a substitute for all history or long-term narrative understanding.

## Reproduce and activate

Outside the restricted sandbox:

```sh
cd /home/sean/projects/edgeloop-ai-fork
.venv/bin/python -m pytest -q tests/ai tests/fork
node --test --test-isolation=none --test-reporter=tap tests/fork/*.test.mjs
.venv/bin/python tools/fork_validate.py --tests --report /tmp/f282-upstream.json
.venv/bin/python -m tests.fork.context_retention_fixture --output /tmp/f282-offline.json
# Optional: uses only existing Ollama; sequential synthetic cases, thinking OFF.
.venv/bin/python -m tests.fork.context_retention_fixture --live --output /tmp/f282-live.json
CONTEXT_BROWSER_REPORT=/tmp/f282-context node tests/fork/context-intelligence-browser.mjs
```

Run the other browser workflows sequentially; several share fixture ports. Use the mock/synthetic fixture modes, not physical devices. When manually running the dashboard browser test, set `FORK_BROWSER_PORT=8890 FORK_OBSERVER_PORT=8898` so it does not use the live 8770/8768 services.

Nothing was restarted during development. When ready, finish any physical session in the original UI and preserve wanted nonpersistent conversation before manually restarting **only** the observer:

```sh
systemctl --user restart edgeloop-ai-observer.service
```

Keep Ollama/web services running and reload the UI. Desktop pairing uses the existing refreshed private pairing file. A manually launched observer can instead be stopped in its own terminal and started with `./tools/serve-ai.sh`; do not start a second observer on an occupied port. No model rebuild or sampling migration is required.
