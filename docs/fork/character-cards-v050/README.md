# Personal Character Cards — isolated v0.5.0 integration review

The personally authored cards are committed unchanged and integrated for testing only. There has been **no merge into `experiment/ai-companion`, no push, publication or export**. This work does not approve the model's dialogue quality.

## Branches and personal integrity

| Item | Value |
| --- | --- |
| Personal worktree | `/home/sean/Work/edgeloop-character-cards` |
| Personal branch | `personal/character-card-edits` |
| Personal edit baseline | `79d6fd0` |
| Personal edit commit | `75d38d8` |
| Preserved local checkpoint tag | `checkpoint/character-cards-personal-20261105` |
| Integration worktree | `/home/sean/Work/edgeloop-character-cards-v050` |
| Integration branch | `test/character-cards-v050` |
| Development HEAD captured for integration | `48530582236b1c6dd2f424569fd802ba8217a658` |
| Local merge commit | `6fdf542cef0f82d40d5a026155b1d18e4d5052ef` |

The integration branch also contains test-fixture maintenance and the simulator review launcher described below. `git log -1 test/character-cards-v050` gives its final review commit. The development branch remains at `4853058`; its worktree was not modified.

Comparison with `79d6fd0` found **27 changed character-card briefs and no other deck changes**. The personally authored brief strings were neither rewritten nor replaced. JSON parsing and the actual schema loader pass. The longest brief is **383 characters**, within the 400-character maximum. All 75 card IDs across the normal and shared special lanes are globally unique.

The normal deck contains **48 Character Cards, twelve for each of Nova, Daisy, Evelyn and Celeste, plus 19 unchanged Common Cards**. All IDs, audiences, intents, eligibility, schema/revision metadata, opening/closing/arrival cards and mission sequences are preserved. There were no merge conflicts. The entire integrated JSON file is byte-for-byte identical to the personal checkpoint, not merely equivalent after parsing.

SHA-256 of the personal and integrated `config/event-deck.json`:

```text
39e04b7cc5362b3c83ca56b9d6c06d9a24a74da79bf07326003cf46eba95c1cb
```

No production Director, observer, compiler, engine, device-control, model-definition or JavaScript application file differs from the captured development base. The only production data change is the merged deck. Existing editorial inventories/transcripts under `docs/fork/character-cards/` describe earlier drafts and are historical, not the current personal content. The authoritative current text is [config/event-deck.json](../../../config/event-deck.json).

## Regression results

| Check | Final result |
| --- | --- |
| Personal branch focused Python suites | **882 passed** |
| Combined integration Python suite | **2,954 passed**, one existing FastAPI/Starlette test-client deprecation warning |
| Engine JavaScript, `npm test` | **50 test files passed**, zero failures/skips; Node's process-isolated reporter counts files |
| Companion JavaScript | **75 passed, one known failure**: presentation alias count, actual 26 / expected 25 |
| Director deck benchmark | Passed existing suite invariants: one inference at a time, zero errors, no tools/thinking, no speech while paused or after stop, character/memory isolation |
| 900-second virtual Director benchmark | Both arms: zero errors, maximum parallel inference one, zero messages after stop, duplicate events suppressed |
| Upstream-sync browser | **Passed**: all current play styles, Bratty Tease, local video + funscript playback and script-mode exit, read-only chat boundary, pause reasons and emergency stop |
| Portrait/character browser | **Passed**: character/model switches, mission-driven expression, cancellation, history restoration, 48 portraits, responsive layouts and emergency stop |
| Character/Director menu browser | **Passed**: settings without inference, story lifecycle, model isolation, responsive menus and accessible emergency controls |
| Real F29 simulator browser | **Passed**: actual F29 reply in RUNNING state, no tools/thinking/agent commands, user emergency stop leaves IDLE with outputs zero |
| Whitespace | `git diff --check` clean |

The known alias-count failure was left unchanged and reproduced on the development baseline. No new persistent product-regression failure remains.

The first integration run exposed test maintenance issues, recorded separately from that known failure:

1. An existing Python test hardcoded the directory name `edgeloop-ai-fork`. It also failed in a detached `4853058` worktree. It now asserts the exact package path in the worktree under test while retaining isolated import checks and rejection of legacy imports.
2. The portrait fixture waited for the retired five-minute event path. It also timed out on unchanged `4853058`. The fixture now uses three actual user-marked simulated edges/resumes, an existing Director mission card and a deterministic mocked response to check the portrait expression.
3. The menu fixture advertised custom ports but connected to hardcoded port 8858. It now honors its existing port parameter. Its goal-change probe activates the original engine control in the same way as the upstream browser fixture, because that element is hidden in the character view. Application UI behavior was not changed.

The new lifecycle sampling harness initially asserted that emergency stop should produce no speech. That assertion was corrected: the required immediate deterministic safety notice must remain, with **zero model calls**. All four final cases satisfy that boundary. This was a harness assertion issue, not a missing safety response.

The final Python suite was rerun after fixture maintenance. Browser cases affected by fixture changes were rerun successfully. Engine and companion JavaScript application code were unchanged after their regression runs.

## Real-model sampling

Only the existing installed F29 aliases on **`http://127.0.0.1:11435`** were used:

- `nova-narrative-f29-v011:latest`
- `daisy-narrative-f29-v014:latest`
- `evelyn-narrative-f29-v013:latest`
- `celeste-narrative-f29-v012:latest`

The endpoint was inactive at the start. Testing temporarily ran the installed Ollama binary on that same port and same model directory, matching the configured one-model/one-inference limits. Pruning and cloud access were disabled. That test-owned process was stopped afterward; no user service definition was edited or enabled.

No Modelfile was rebuilt and no model was pulled, created or deleted. The before/after model-store audit contains the same **78 files**, with unchanged sizes/timestamps and unchanged manifest hashes. No stored-model change was observed. Runtime loading/unloading only affects memory.

All inference used the real service/compiler, thinking off, no tools, temperature 0.4 and the existing output budget. Every session observation was synthetic. Running scenarios start at two edges / 600 seconds and five edges / 1300 seconds, with timestamped simulated HR at 90 BPM. They are not physical measurements. No physical device was connected or operated.

### Coverage and delivery

- **96 main replies:** two for each personal Character Card; all delivered, no conversation errors or final suppressions. 105 provider calls include bounded retries.
- **Eight previous-message controls:** original name/brevity question versus no prior user message, one pair per companion.
- **32 shared-lane replies:** every companion sampled first/returning/unknown-history Arrival, Opening, each of the three edge missions and Closing. All delivered; no conversation errors or final suppressions. 35 provider calls include retries.
- **Four emergency-stop cases:** deterministic safety notice, zero model requests.
- Standard eligibility and unweighted shuffle cycles are checked separately by regression tests. Live coverage isolates one card at a time and reverses the second scenario's order; it is not a natural full-session conversation or a frequency/reliability estimate.

Each normal-card sample's recorded brief was checked against the integrated authored text. All 48 cards appear exactly twice and use the correct F29 character. The existing memory and eligibility checks remain intact.

### Representative delivered dialogue

These are verbatim model outputs, not rewritten briefs. They illustrate both character voice and context problems; other replies and all outgoing requests are in the local raw evidence.

**Nova, chosen-name:**

> I chose Nova because it sounds like a star that refuses to stay in its designated orbit, a name I stole from the cosmos to claim my own shape. Tell me, does that name feel as grand to you as it does to me?

**Daisy, farm-future:**

> I reckon Cloverfield can keep this program humming while still feeling like a proper family place. It's a juggling act, but I intend to make the ledger look good without losing our soul.

**Evelyn, research-ambition:**

> I intend to earn my keep by asking questions that matter, rather than drowning your biology in my own decorative jargon. If my paper boat of theory floats, let it be because I finally found the right words.

That paper-boat callback is contamination from the answered naming request, not a requested part of the card.

**Celeste, public-promise:**

> I intend this mission to prove that our future families deserve the fertile promise we were denied, not merely the convenient metrics of a contractor's ledger.

### Remaining dialogue-context issues

**27/96** main replies contain one of the deliberately distinctive earlier-message markers. This is a lexical review aid: it is neither an exhaustive detector nor proof of contamination for every flagged word. Clear examples still answer or borrow the earlier boat/café naming task. The default compiler retains that answered user text as labelled background in the current provider user-role block. This integration did not change that policy.

**33/96** main replies end in a question; mean length is **34.2 words**. Lexical counts do not measure personality fidelity or dialogue quality.

The samples still invent shared history, perceived behavior or participant traits. Some mission replies infer rarity, discipline, endurance or statistical significance from an engine edge count. Returning Arrival and Closing replies can attach unsupported motives to the participant's decision to stop. These are language-grounding failures, even when the correct count/time is included and the transport accepts the reply. They do not establish real measurements or scientific findings.

First-session Arrival, denied history and no-prior-message controls distinguish supplied history from invented familiarity, but do not eliminate the failures. A separate coordinated compiler/model-context investigation remains warranted. Your authored content is preserved; concerns are reported here rather than edited into it.

## Launch the integrated build for a simulator-only review

This worktree already has a local Python environment and the existing Playwright dependency available. Its isolated Python import check resolves `ai_observer` and `companion_ai` to this integration worktree, including under `-I`; it does not silently import the development checkout. Dependencies are reused locally without downloading or replacing them.

Start only the existing installed Ollama service, then launch the review window from the **integration** worktree:

```bash
systemctl --user start edgeloop-ai-ollama.service
cd /home/sean/Work/edgeloop-character-cards-v050
node tools/review-character-cards.mjs
```

The launcher requires the four already-installed F29 aliases on port 11435. It does not install or rebuild them. If Ollama is still starting, wait until `http://127.0.0.1:11435/api/tags` responds and rerun the launcher.

It opens its own Chromium window, integrated UI on port **18970** and temporary read-only observer on **18968**. HR is simulated, device readiness/commands are mocked, native Bluetooth/serial/USB/HID permissions are denied and non-observer sockets/external page requests are blocked. Agent-driven controls remain absent. The companion still cannot issue engine commands.

Use **Play** in that window to begin. Select any of the four F29 companions, let the normal deck shuffle, chat normally, change simulator values or try the upstream video/script controls. Emergency Stop remains the original user-operated engine control. The launcher does not start a running session automatically in interactive mode.

**Use the window opened by this launcher.** Do not open its URL in a separate ordinary browser tab: interception and device-denial guards belong to the review browser context, not the underlying normal application. Close the window or press Ctrl+C to stop its UI/observer fixtures. Review settings and conversation history are temporary; the committed card file is untouched. The separately started Ollama service remains under your control.

A repeatable headless smoke check is also available:

```bash
EDGELOOP_REVIEW_REPORT=/tmp/edgeloop-v050-review \
  node tools/review-character-cards.mjs --smoke
```

## Local evidence and repeat commands

Full logs, raw requests, browser reports/screenshots and before/after audits are in:

```text
/home/sean/Work/character-cards-v050-validation/
```

[Machine-readable integration summary](summary.json) includes exact results and report paths. The full local summary adds the final integration HEAD after the commit is created. Important raw files are `real-character-cards.json`, `real-lifecycle-final.json`, `python-full-final.log`, `javascript-engine.log`, `javascript-companion.log` and the four passing `browser-*/report.json` files. Original failing/baseline fixture logs are retained separately. Raw request evidence records its historical harness base and an explicit provenance block for this personal checkpoint/integration merge.

```bash
.venv/bin/python -m pytest -q
npm test
node --test --test-isolation=none tests/fork/*.test.mjs
.venv/bin/python -m tests.fork.deck_session_benchmark --output /tmp/v050-deck.json
EDGELOOP_LIVE_ACCEPTANCE=1 .venv/bin/python -m tests.fork.character_cards_smoke \
  --url http://127.0.0.1:11435 --diagnostics --output /tmp/v050-cards.json
EDGELOOP_LIVE_ACCEPTANCE=1 .venv/bin/python -m tests.fork.character_cards_lifecycle_smoke \
  --output /tmp/v050-lifecycle.json
```

Stop here for personal review. No merge into development is authorized by these test results alone; the development branch remains untouched.
