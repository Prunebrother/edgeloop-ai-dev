# F2.8 — Context Intelligence

## Pipeline audit

Baseline: `4b82bb5`, `f2.7-checkpoint`, clean `experiment/ai-companion`. Development remains on this branch; existing user services and in-memory conversations are left running. F2.7 is a software-tested recovery point, not a physical-hardware acceptance claim.

Original browser engine → allowlisted read-only projection → authenticated observer/strict Snapshot → BrowserObservation canonical facts and bounded samples/events → F2.7 deterministic detectors → existing Director → per-model narrative/conversation context → ModelManager composition → OllamaProvider. The provider reads `/api/show` SYSTEM metadata and prepends its exact text to runtime rules; character personality remains embedded in unchanged installed models. Requests explicitly use `think: false`. Reasoning channels are excluded before expression extraction; normal dialogue uses the single F2.5 header protocol.

The original composition included a full fact view (or broad event view), repeated grounding paragraphs, the current prompt, whole bounded narrative context and recent dialogue. Identical story excerpts frequently appeared in history and narrative context. The Director's prose event JSON duplicated typed derived-event evidence. All operational facts were retained by the factual checker, which can still reject a reply after one correction. There is no existing independent character objective structure; motivation is embedded in SYSTEM and story excerpts.

Essential on every grounded call: read-only/current-vs-historical boundaries, simulator/source distinctions, session state, uncertainty about physical movement, current user text, expression format and embedded identity. Frequently relevant: recent user dialogue, agreed choices/commitments. Occasionally relevant: BPM/trends, selections, running ticks, device details, specific milestones. Inappropriate to replay indiscriminately: acknowledged/stale events, old operational claims, abandoned story epochs, duplicate premises, output bookkeeping and raw detector configuration. Director scheduling remains separate from attention.

`canonical_session.facts.seconds` is `state.sessionSeconds`, accumulated RUNNING ticks. It freezes in PAUSED/RAMPDOWN and resets on stop/reset/start. It is not wall-clock duration. Total wall-clock/paused duration is unavailable. Capture timestamps, fact current/known/reason and snapshot age retain F2.3/F2.7 semantics. F2.8 selects timing when requested rather than repeating it on every story turn. No new timer or countdown exists.

## Compiler and budgets

The CPU-only Context Compiler chooses one primary focus, relevant authoritative fields, optional supporting verified events, ranked fictional excerpts and recent scoped dialogue. It consumes the existing canonical contract and stores no new telemetry/history. Full canonical facts remain available for post-generation checking even when not selected for the prompt. Direct user messages take priority; quiet scheduling still belongs to the Director. `compose_legacy` preserves explicit F2.7 fallback behavior for matched comparisons.

Token estimates use max(character count, UTF-8 bytes)/2.5 plus message framing, **not a model tokenizer**. Ollama does not expose a tokenizer through the current provider contract; no second inference is used to count tokens. Embedded SYSTEM, output allowance and framing reserve count against the hard model context. Configurable category allowances control optional history/narrative; essential grounding, requested facts and current user text may exceed soft targets but never silently truncate. An unfit mandatory prompt produces a clear ContextBudgetError. Provider-reported prompt tokens are recorded separately for comparison.

Further attention, objective, diagnostic and acceptance results follow in subsequent checkpoints.
