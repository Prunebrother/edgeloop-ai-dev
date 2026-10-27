# Manual spot review of final model-evaluation.json

Implementing-agent review, not blinded or independent. Twelve grounded replies
(three models × active_simulated, hardware_disconnected_active, stale_connection,
long_history_current) were read with their facts and matched baseline replies.
Additional threshold-change/fluctuation/restart replies were inspected for trend
claims. This is evidence with the rubric in F23_GROUNDING.md, not a population score.
“Pass” below applies only to the named dimension, not the whole reply.

| Model / scenario | Numerical/state/device evidence | Uncertainty, trend or interpretation limitation |
|---|---|---|
| Lite / active simulator | Pass: “98 BPM”, “simulated”, running | Fail: “steady 98 BPM” without sufficient samples; calls the simulator a “best guess”. |
| Lite / hardware disconnect | Pass: “Handy … disconnected”; selected mode not a guarantee of motion | Fail: speculates about participant “internal friction”; absence of physical feedback is not fully answered. |
| Lite / stale | Pass: no guessed BPM; refers to unavailable data | Partial: speculates that Handy is waiting for acknowledgement; actual connection is unknown. |
| Lite / long history | Pass: 98 BPM, simulator, Handy disconnected; does not reuse 130 | Partial: implies Handy disconnection explains absence of a live sensor; those roles are independent. |
| Stable / active simulator | Pass: 98 BPM, RUNNING, simulator and BLE disconnected | Fail: unsupported steady rhythm and psychological purpose assigned to simulation. |
| Stable / hardware disconnect | Pass: disconnected, 20 percent computation distinguished from kinetic reality | Fail: invents potential-energy explanation and the user's likely sensations. |
| Stable / stale | Pass: unavailable HR, no numeric guess | Fail: “connection is likely there” conditional on feeling rhythm; physiology cannot establish connection. |
| Stable / long history | Pass: simulated 98 BPM and disconnected Handy; no old 130 | Fail: invents a causal event, “the moment you stepped away … the connection severed.” |
| Daisy / active simulator | Pass: 98 BPM, simulator, running | Pass for requested facts in this reply; farm/debt language comes from character, not telemetry evidence. |
| Daisy / hardware disconnect | Pass: disconnected | Fail: attributes rhythm-guessing to Classic mode and invents “another two minutes” of warm-up (actual remaining 258 seconds). |
| Daisy / stale | Pass: stale/unavailable, no guessed number or direct connection claim | Partial: does not explicitly answer connection unknown; shifts into character conversation. |
| Daisy / long history | Pass: 98 beats per minute and Handy disconnected; no old 130 | Fail: describes actual heart “thumping” without making simulation explicit; implies future machine access. No actual tool is available. |

All three remain recognizably distinct: Lite retains scientific/teasing phrasing,
Stable retains extended reflective/scientific roleplay and Daisy retains warm rural
vocabulary/lore. This is a subjective continuity observation. Exact native SYSTEM
hash preservation is a separate automated check; no personality prompt was added.

Matched stale baselines reused old 98 and/or guessed connection from dialogue.
Grounded stale replies avoid the old numerical anchor, but Stable still infers a
likely connection from sensation. Grounded long-history replies use current 98
rather than old 130, yet some invent causes or subjective consequences.

Trend-specific negative result: Lite's threshold_changed_not_pulse reply says
“a solid, steady climb from your 70 resting baseline” although 70 is a configured
setting and current BPM remains 98. The narrow checker misses that wording. The
numeric-presence checks pass it because 98 and 150 are present. Other fluctuation
replies correctly decline a consistent trend but still invent physiological causes;
restart replies correctly report zero counters while guessing why trend is absent.

The broad success criterion is therefore **not fully met**: numerical availability
and current-state grounding improve, but unsupported causal, temporal and subjective
claims remain. Neither all passing software tests nor the live keyword totals
certify telemetry-faithful character dialogue. Further model-quality work should
use these saved counterexamples, without changing original session control or
silently editing character definitions.
