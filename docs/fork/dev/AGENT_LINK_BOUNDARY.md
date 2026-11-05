# Agent Link: integration boundary (not integrated)

Status, 2026-11-05: **not part of this fork.** The upstream sync on `feature/upstream-sync` takes `upstream/main` (`d3c5df3`, EdgeLoop 1.1.4.31 + 2 fixes). Agent Link exists only on `upstream/dev`, so it was not pulled in. This document records what it depends on and the boundary any future implementation must keep. Guard tests fail if Agent Link code arrives with a later sync (see "Guards in place").

## What upstream's Agent Link is

Upstream commit `d65a84d` ("add an agent link beside Share Control"), on `upstream/dev` only, plus later relay commits:

| Part | File | Role |
|---|---|---|
| Control document | `src/js/agent-api.js` | Pure builder for the JSON an agent GETs: menu of play styles, games, endgames, durations and loops, plus live heart rate, speeds and toys. Also `AGENT_INSTRUCTIONS` and the command list. |
| Host wiring | `src/js/app.js` (~220 lines) | `startAgentLink()` mints a token and opens a WebSocket to the relay. It pushes state and telemetry. Incoming `command` messages go through `routeHostCommand(cmd,'controller')` and then `applySharedCommand()`. |
| Command validation | `src/js/peer-messages.js` | Same validator a human remote controller uses (adds `DURATION` bounds). |
| Relay | `worker/index.js`, `wrangler.jsonc` | Cloudflare Worker + Durable Object `AgentRoom` at `/api/agent/<token>`. GET returns the document; POST forwards one command. CORS `*`. |
| Client | `tools/edgeloop_openwebui.py` | Open WebUI tool. Read the session, POST a command. |

Commands an agent can send:
- `SESSION_STATE` (RUNNING/PAUSED/IDLE)
- `SESSION_RESET`
- `MODE_CHANGE`
- `ENDGAME`
- `DURATION`
- `INTENSITY`
- `SPEED_WINDOW`
- `ORGASM_TOGGLE`
- `EDGE_MARK`
- `MANUAL_PATTERN`, which moves toys through a named loop

How upstream treats access and safety:
- **Credential:** the 22-character token in the URL path is the only credential.
- **Activation:** the agent link starts **automatically whenever Share Control starts** (`setupPartnerHost()` calls `startAgentLink()`). It is not separately opt-in.
- **Safety:** commands are applied like a human remote controller's. Heart-rate feedback and the engine's own rules still run, and the agent cannot set the climax heart rate.

### Dependencies that block a minimal, isolated port

- `agent-api.js` imports `sanitizeDeviceCatalog` and `PATTERN_IDS` from `src/js/manual-control.js`. That file comes from the Share Control controller/controllee rework (`432e5ba`, `8ba0441`, …), which is also dev-only and not in this sync.
- Transport is the Cloudflare relay (`/api/agent`, `/api/room`). The local server (`tools/serve_local.py`) serves no `/api/*` path, and a local equivalent would be new infrastructure.
- Host wiring is spread through the Share Control code in `app.js`.

**Conclusion:** no part of Agent Link can be integrated now without pulling in dev-only Share Control code or building new transport. Per the architectural decision, no unused agent infrastructure or Cloudflare dependency is added for future extensibility.

## Required boundary for any future implementation

These follow the 2026-11-05 architectural decisions. All are mandatory.

1. **Off by default; explicit opt-in.** A separate setting, never implied by Share Control or by the AI companion being connected. It is enabled per session, shows a visible indicator, and turns off again on stop, reload and reset.
2. **Inactive on the network when disabled.** No listener, socket, poll timer or relay registration exists until opt-in. A test asserts zero agent traffic with the setting off.
3. **Authenticated.**
   - Loopback-only by default (`127.0.0.1`), with exact Host/Origin checks like `/ai/pair`.
   - A per-session random token that is never placed in a URL path, log, snapshot, history or export.
   - Rejection of unauthenticated or replayed requests, plus rate limiting.
   - Any remote relay is a separate, later decision.
4. **Requests, never commands.** An agent submits a *request*. The deterministic EdgeLoop engine decides; the agent never reaches a driver. Engine-authorized path:

   ```
   agent request ──► authenticate ──► parse (closed schema, bounded values)
                 ──► engine authorizer (pure, deterministic):
                       allowlisted request types only
                       session preconditions (e.g. duration only while IDLE)
                       device limits, session rules, guards, ceiling/crawl, HR watchdog
                       emergency stop and Stop always win; nothing re-arms after a safety stop
                 ──► optional user confirmation (policy per request type)
                 ──► existing engine handler (same code path as the on-page control)
                 ──► outcome visible only through the normal read-only snapshot
   ```

5. **Non-overridable safeguards.** No request may change or bypass:
   - heart-rate limits and calibration
   - the HR watchdog and stale-signal pause
   - stall guard, ceiling or crawl behaviour
   - device caps and per-device limits
   - session rules or the emergency stop

   Manual motion patterns (`MANUAL_PATTERN`) and `ORGASM_TOGGLE` stay excluded unless separately approved. There is no sensorless operation: the heart-rate requirement is unchanged.
6. **Director 2.0 stays read-only.** The companion service (`ai_observer`, `companion_ai`, `src/js/ai/**`) never gets an agent credential, request API or command type. The observer protocol stays closed (no command message types). An agent integration would be a separate component with its own credential and its own audit log.
7. **Audit.** Every request and decision (accepted, rejected and why) is recorded locally and kept out of AI memory and exports.

### Opt-in configuration (sketch, not implemented)

```json
{
  "agent_link": {
    "enabled": false,
    "bind": "127.0.0.1",
    "requests": ["SESSION_STATE:PAUSED", "SESSION_STATE:IDLE", "ENDGAME", "DURATION"],
    "confirm": {"SESSION_STATE:RUNNING": "always", "INTENSITY": "always"},
    "rate_limit_per_minute": 20
  }
}
```

The setting belongs to the engine's settings, never to the companion's configuration.

### Tests required before any merge

- Disabled by default: no listener, socket, timer or request with the setting off (browser fixture with request interception).
- Unauthorized requests are rejected: missing or wrong token, wrong Origin/Host, replay, rate limit, unknown type, out-of-range value.
- Safeguards stay authoritative: every non-overridable item above has a test where a request tries it and the engine refuses.
- Emergency stop during an agent session stops and stays stopped.
- The observer protocol and `src/js/ai/**` still carry no command types (the existing guards).

## Guards in place on this branch

- `tests/fork/upstream-sync-guards.test.mjs`:
  - fails if `src/js/agent-api.js`, `worker/` or `tools/edgeloop_openwebui.py` exists, or if `app.js`, `index.html` or `sw.js` contains agent-link code
  - fails if `src/js/ai/**` imports engine, driver or transport modules, or contains session-command or agent primitives
- `tests/fork/test_upstream_sync_guards.py`:
  - the observer protocol is a closed set with no engine command types
  - the observer server never emits engine commands
  - the local server serves no `/api/agent`, `/api/room` or `worker` path
- `tests/fork/upstream-sync-browser.mjs`: fails if the page contacts `/api/agent` or `/api/room`.
- `tools/public-source-rules.json` and `docs/fork/release-exclusions.json` already omit the Cloudflare deployment file (`wrangler.jsonc`).

A future, approved Agent Link change must replace the "absent" guard with tests for the boundary above. It must not delete the guard on its own.
