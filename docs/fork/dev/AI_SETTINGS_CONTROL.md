# AI Settings Control (v0.6.0, in development)

Status, 2026-11-05: approved by the user, being built on `feature/ai-settings-control`. This changes the earlier rule that the companion is strictly read-only (see [AGENT_LINK_BOUNDARY.md](AGENT_LINK_BOUNDARY.md)). The safety wording is in [SAFETY.md](../../../SAFETY.md).

## Goal

A companion model may change a few session settings itself, in character, for a more engaging session. The engine stays the only hardware authority. Every change is announced by a settings card in the character's voice.

## User decisions (2026-11-05)

- Off by default. When the user turns it on, the default mode is **auto** (changes apply without a confirmation step).
- Allowed: play style, game, **endgame**, **orgasm toggle**, intensity inside a user-set band, pause and stop.
- Every applied change plays a card saying what the character did and why, according to its personality.
- Target release: v0.6.0.

## Implementation decisions

- Upstream's `agent-api.js`, Cloudflare worker and Open WebUI tool are **not** pulled in. `agent-api.js` depends on dev-only Share Control code. The fork uses its own small request vocabulary instead.
- The speed window is left out of v0.6.0. It is a persisted user setting, so an AI change would overwrite the user's own limits.
- Calibration and script mode are never selectable by the AI.

## Flow

```
Observer (Python)                                 Browser
-----------------                                 -------
settings decision pass (JSON schema, think:false)
  -> {setting, value, reason} or none
  -> settings_request ───────────────────────────► src/js/ai/connection.js (opaque forward)
                                                    -> engine-side gate (src/js/ai-settings/gate.js, pure)
                                                    -> same handler as the on-page control (app.js)
                                                    -> change chip with Undo, audit entry
  ◄─────────────────────────────── settings_outcome {applied | rejected, reason, from, to}
  ◄─────────────────────────────── next observation: details.ai_settings shows the applied change
confirmed in the snapshot?
  -> settings card (Director queue, Player-event card path)
     brief = confirmed change + the model's private reason
```

The card is generated only after the authoritative snapshot confirms the change, so it never announces something the gate rejected or clamped differently.

## Gate rules (engine side, authoritative)

A request is rejected unless all of these hold:

- AI Settings Control is enabled and has not been revoked for this session. Emergency stop revokes it.
- The request's `session_id` matches the live session.
- The session is RUNNING (pause also in RAMPDOWN, stop also in PAUSED).
- The heart-rate signal is fresh and the toy is ready. Pause and stop skip these checks, because they only reduce stimulation.
- At least `min_interval_seconds` (default 45) have passed since the last applied change. Pause and stop are exempt.
- The setting is on the allowlist, the value is valid, and the value differs from the current one.
- The page is not a remote viewer or controller page.

Intensity is clamped into the user's band (default 20–80 on the 0–100 slider). The outcome reports the value actually applied.

The AI can never start or resume a session, reset, change duration, stream motion, change heart-rate limits or calibration, select devices, or touch the speed window.

## Python side

- `companion_ai/settings_control.py`: the decision prompt and schema, cadence (only while the snapshot says it is enabled and RUNNING; at most one decision every `decision_interval_seconds`; also after an edge and after a user message), the pending-request ledger and the snapshot confirmation.
- The observer protocol gains exactly two message types: `settings_request` (server → browser) and `settings_outcome` (browser → server). Neither carries engine command names.
- Settings cards use the Player-event card path, with priority above ordinary event cards. They are announced even when spontaneous commentary is off, because they report the model's own action.

## Tests required before merge

- The gate: every forbidden setting, every precondition, clamping, rate limiting, revocation after emergency stop, garbage input.
- The guards are updated, not deleted: `src/js/ai/**` still has no engine imports or command names, and the protocol adds only the two new types.
- Python: decision schema parsing with malformed model output, the confirmation logic, card briefs.
- Browser acceptance on the isolated fixture ports only.
- Garbage-output runs with the four F29 models, then hardware testing by the user.
