# Thinking response completion repair

Thinking and visible answers share Ollama's output-token budget. The provider
previously accepted `done_reason: "length"` whenever any visible text existed,
presenting an unfinished answer as successful and storing it in memory. Only
reasoning-only exhaustion received the existing bounded retry.

The provider now detects incomplete visible responses. Thinking requests get one
retry with twice the output budget, capped at 4096, within the original deadline.
The existing response-start message replaces the partial bubble before the retry;
no partial draft or private reasoning is retained in conversation memory. If the
retry also reaches its limit, the UI shows an explicit incomplete-response error.
Thinking is never silently disabled and embedded Modelfile instructions are unchanged.
No session, device, authentication or protocol-validation rules changed.

Validation: 94 Python tests passed, including partial-reply replacement, exhausted
retry, non-thinking truncation, shared deadlines and previous reasoning-only retry.
Chromium acceptance passed with a dedicated cutoff/retry fixture and the full
session/responsive checks. Upstream source validation passed.

A real thinking-enabled Evelyn Lite Candidate test on port 11435 completed with
`done_reason: "stop"`, using 3567 output tokens after a 2048-to-4096 reasoning-only
retry. This demonstrates that reasoning can consume the initial budget, but does
not establish the exact cause of the user's individual reply without its prompt.
The partial-visible failure and repair are reproduced deterministically by tests.

The post-fix live test also ended naturally (`stop`), with 3063 output tokens
and thinking still enabled. Its telemetry keyword check returned false because
the model spelled out ninety-eight; this is a streaming/completion pass, not a
character-quality guarantee. Reports are in `f22/thinking-completion/`.
