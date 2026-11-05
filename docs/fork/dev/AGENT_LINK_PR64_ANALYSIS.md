# Upstream Agent Link (PR 64) and AI Settings Control

Status: analysis, 2026-11-05. No code depends on PR 64.

Upstream PR 64 (`cursor/agent-companion-snapshot-1d7b` → `dev`, +292/−145, version 1.1.5.37) extends the Agent Link: `GET https://dev.edgeloop.app/api/agent/<22-char token>` returns an `edgeloop-control v1` document (companion, state, menu, commands, instructions), and `POST` sends commands. The upstream developer suggests we keep the observer protocol read-only, add no command types to `ai_observer` or `src/js/ai`, and have the companion talk HTTP or WebSocket to that URL only.

## Where it agrees with our design

- The engine stays the authority: heart-rate limits, watchdog, caps and emergency stop apply to agent commands too. That's the same principle as our gate.
- Commands go through the page's normal handlers. PR 64 adds an `agent` source to `applyModeSelection`, which matches our `selection_source: 'ai'` labelling.
- Our seven settings map onto a subset of its commands: MODE_CHANGE (play style, game), ENDGAME, ORGASM_TOGGLE, INTENSITY, SESSION_STATE (pause, stop).

## Where it does not fit (today)

| Our requirement | Agent Link (PR 64) |
|---|---|
| Local and offline; session data stays on the machine | Cloudflare relay on the public internet, PeerJS to the page |
| Off by default, explicit opt-in | Active whenever Share Control is on |
| Narrow, engine-side allowlist (no start/resume, duration, speed window, motion) | SESSION_STATE, SESSION_RESET, DURATION, SPEED_WINDOW, EDGE_MARK, MANUAL_PATTERN are all accepted. Any restriction would live in our Python only, outside the engine. |
| Pacing for own changes, a minimum interval, an intensity band, ask mode, undo | 400 commands per 10 s transport limit only |
| Emergency stop revokes AI control for the session | Not specified for the link |
| Stale-session check, `trigger` and outcome read-back for honest cards | The document lacks session_id, trend, Player facts, warmup and terminal outcome |
| Credential not exposed | The token in the URL is the only credential (ends up in logs and history) |
| We track `main` releases | `dev` only, not released |

Because the companion document lacks session_id, trend and Player facts, we would still need the observer for reading. Two channels (observer for reads, relay for writes) can't confirm that a command hit the session the model saw.

## The protocol question

The developer's advice ("observer read-only, no command types") differs from the design you approved for v0.6.0, which adds exactly two message types (`settings_request`, `settings_outcome`). Neither type carries engine command names. `src/js/ai/**` forwards them opaquely to the engine-side gate in `src/js/ai-settings/`, and the guard tests enforce both. With AI Settings Control off, the observer is still read-only. The developer's concern (the observer turning into a command channel) is covered by the gate. Routing through the relay would remove our gate from the path.

## Recommendation

1. v0.6.0 ships with the local gate as built. Don't route through the public relay.
2. Keep the request/outcome interface in `companion_ai/settings_control.py` transport-neutral, so an Agent Link adapter can be added later behind the same gate rules.
3. Ask upstream for the points below. If they land in `main`, revisit (v0.7+).

## Reply draft to the upstream developer

> Thanks, this is useful. We read PR 64 closely. Our AI companion runs fully local (Ollama on the same machine), so for our fork a few things would need to change before we could use the Agent Link as the write path:
>
> 1. A loopback transport (e.g. `ws://127.0.0.1/...` from the page itself), so nothing leaves the machine and no internet connection is needed.
> 2. A per-link command allowlist set on the host. We allow only mode/game, endgame, orgasm toggle, intensity within a user-set band, pause and stop, and never SESSION_STATE start/resume, SESSION_RESET, DURATION, SPEED_WINDOW or MANUAL_PATTERN.
> 3. Explicit opt-in separate from Share Control, and revocation on emergency stop.
> 4. The token in a header rather than the URL.
> 5. session_id (and ideally an outcome read-back per command) in the companion document.
>
> Until then we keep a small local gate in the page that applies the same handlers as the on-page controls, labels changes as AI-made, and stays off by default. The `agent` source in applyModeSelection is a good idea; we'd reuse it for our label once it's in main.
