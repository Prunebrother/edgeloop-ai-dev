# F2.8.4 — Persistent Session Journal

Starting HEAD: `2781e8a` (`f2.8.3-checkpoint`), clean `experiment/ai-companion`. Development stayed on that branch. Existing models, Modelfiles, portraits, conversations and services were preserved. The original engine, hardware commands and safety algorithms were not changed. The only upstream-file edit is the public service-worker module precache/version, recorded in the reviewed-change manifest.

## Capture and persistence

Previously, completed summaries existed only in an eight-entry observer deque, with three entries exposed to the model observing termination. Observer restart lost them. The live sample deque resets at status/source boundaries and therefore cannot supply a reliable session-wide HR range.

`SessionJournal` consumes accepted `BrowserObservation` snapshots and the existing pre-reset completed summary. It does not subscribe to another telemetry stream or infer a session controller. A small active accumulator keeps only aggregates, bounded setting changes and validated event references. One atomic JSON write occurs at completion, not on every tick.

Records contain:

- Engine session ID; observed start timestamp in timezone-aware UTC, or unknown when the observer did not see a start. First-observed time is separately labelled and never substituted for the start.
- Verified active running duration from the existing pre-reset summary. Pause does not advance this counter. If final capture is incomplete, final duration remains unknown; partial last-verified ticks remain explicitly separate. No wall-clock or paused duration is inferred.
- Companion/model participation, including switches, with bounded provenance. Model scopes support identity isolation. A single record represents the session even when more than one companion participated.
- Completion status: unknown, explicit user report, or validated accepted application event. Ordinary stop never proves completion. Accepted application events and early-release reports are not physiological diagnoses. Survival completion can be retained without falsely terminating its running session.
- Separate physical BLE and simulator HR min/max aggregates, distinct sample counts and source/quality labels. Only observer-valid, timestamped samples count. Stale/disconnected values and duplicate sample stamps do not add samples. Ranges are observed samples, not complete physiological coverage.
- Verified final edges, experience/goal, selected intensity, stroke bounds and available HR configuration limits; bounded setting changes and verified event kinds/timestamps. Settings are original engine configuration, never proof of physical hardware action.
- Stop classification, final telemetry timestamp, final-counter confidence and quality flags for missing start, gaps, missing timestamps, unavailable sensors and truncation.

Future experiment fields distinguish character proposals, user approvals, engine configuration and observations. Proposal/approval fields remain null. There is no proposal execution, autonomous adjustment or new model call.

The existing `SettingsStore` writes `session-journal.json` under `EDGELOOP_FORK_AI_DATA` (default `.ai-data/`) using a private temporary file, fsync and atomic replacement. The journal holds at most 100 completed records, 32 setting changes, 32 event references and 16 companion identities per session; truncation is marked. Up to 256 opaque closed-session IDs prevent replay after deletion, reconnect and restart. Deletion/clear remove session facts; these bounded deduplication identifiers contain no timestamps, measurements or narrative content.

Recording and AI historical access both default **off**, independently. Disabling recording discards the active accumulator and preserves existing records. Enabling midway produces an incomplete-start record. Starting a new fictional storyline does not touch the journal. No credentials, pairing tokens, conversation text or raw telemetry series are stored. The journal is local and unencrypted, using the project's existing storage convention; local filesystem access determines who can read it.

Completed records survive observer restart and browser reload. An observer restart during a running session starts a partial accumulator on its next accepted running observation. A stop that occurs entirely while disconnected cannot be reconstructed. There is no retroactive import of old conversations or ephemeral summaries. Storage failures preserve the existing file, stop recording and expose an error without changing physical stopping. Corrupt/unsupported journal files are preserved and access defaults off; repair or restore that file manually before re-enabling recording. Use one observer writer per data directory.

## Interface and privacy

The authenticated observer WebSocket adds a strict `session_journal` message with get/configure/delete/clear/report-completion actions. It shares existing origin, pairing, size and ownership checks. Invalid actions cannot reach EdgeLoop hardware. Journal mutation cancels an in-flight companion response, so a response using deleted/disabled historical evidence cannot complete after the mutation.

The Session Journal button opens an existing-style drawer. The table sorts by date, companion, duration, edges, completion, HR minimum, experience and goal, with ten records per page. A row opens readable observations, selected settings, setting changes, quality and validated events. Simulator sources remain visibly labelled. Users can report completion explicitly, delete one record or confirm clearing all records. Recording and AI access have separate checkboxes. The toolbar wraps and the table scrolls within the drawer, preserving the portrait and three-column layout. Browser rendering remains unverified in this environment.

Only public JavaScript is precached. Journal data is returned through the authenticated socket when requested, not embedded in static files or the service-worker cache.

## Historical context and factual validation

Relevant historical session questions select one record, or two for comparison, with a compact field projection. HR ranges are included only for HR questions; settings and up to six recent changes only for settings/comparison questions. Generic comparison also supplies current running time, edges and selected settings. All historical facts are explicitly separated from current telemetry and reset counters.

Default retrieval is limited to the exact model scope that participated. An explicit named-character request can share that character's factual sessions with another character, as indicated in the privacy controls; fictional Story Memory remains isolated. Evelyn, Daisy and Celeste have deterministic named lookup support. Future models use the same default scope isolation without character-specific schema changes.

The Context Compiler reports selected journal session IDs. It preserves existing dialogue/story allocation and hard context limits. Greetings and unrelated fictional recall do not receive journal records. Missing matching records produce an explicit unavailable-evidence instruction rather than silently substituting another companion's ephemeral summary. Disabling historical AI access blocks historical completed-summary context and operational transcript fallback for recall questions, while leaving immediate authoritative completion-event reactions intact. It does not erase transcripts or prevent discussion of details the user supplies in the current message.

The existing factual validator can check historical duration and explicitly labelled HR extrema against selected records without authorizing a current measurement. Historical simulated readings never establish the user's physiology. No broader model rewrite or second validation inference was added; `think: false` and the existing expression/streaming/cancellation paths remain intact.

## Validation and performance

Artifacts: [synthetic comparison](f284/evaluation.json), [regression summary](f284/validation.json), [upstream suite](f284/upstream-tests.json), [browser attempts](f284/browser-results.json).

- **1,057 upstream tests pass**, with zero failed files and the original-file manifest verified.
- **533 Python tests pass**, including 29 new journal cases. Three pre-existing TCP-dependent cases are environment-blocked: occupied observer port, occupied UI port and desktop HTTP pairing. The unfiltered attempt reproduced the two failures and one fixture error with `EPERM`; the final run deselects those three. As in F2.8.3, an external `/tmp`-only 20 ms selector polling shim lets in-process TestClient work despite denied asyncio self-pipe writes. Production code does not use that shim. One existing Starlette deprecation warning remains.
- **44 companion JavaScript tests pass**, including two new table-format cases. These do not substitute for DOM/browser validation.
- All seven existing browser workflows and the new journal workflow were attempted on isolated fixture ports. **Eight are blocked** before acceptance by denied sockets/Chromium IPC. No browser screenshots or responsive-layout pass is claimed.
- Three limited sequential attempts used the existing Ollama endpoint, Evelyn v1, Daisy v1 and Celeste v2, always with thinking off. **All are blocked by `ConnectError`; zero generations occurred.** Actual provider tokens, inference latency, VRAM and subjective narrative quality remain unmeasured.

The matched compilation benchmark loads the actual F2.8.3 compiler from Git and uses identical synthetic histories and native-source identity lengths for all three characters, with 30 repetitions per scenario. Greetings have identical estimated prompt sizes. Six historical duration/settings scenarios select the journal in F2.8.4 versus zero in F2.8.3. Relevant prompts add approximately 365–437 estimated tokens; two recent dialogue messages remain retained. Settings cases retain the same two story items; timing cases retain none in both versions because they are unrelated. These are retrieval/compilation measurements, not generated-answer accuracy. UTF-8/character estimates are conservative and are not tokenizer-exact. See the artifact for measured compilation medians and atomic-write latency; no global context target was increased.

Remaining limits: English keyword retrieval can miss paraphrases. Bounded projections can omit older setting changes or events. HR extrema describe valid observed samples, with possible gaps. Model changes not followed by an accepted telemetry observation cannot be timed precisely. Existing post-generation checks catch narrow objective claims, not every possible invented historical statement. Correct evidence does not guarantee faithful generation. Physical safety behavior was preserved, not revalidated by hardware testing.

## Activation and reproduction

No active service was restarted. When ready, manually stop the existing observer and launch the updated observer with the **same data directory**; leave Ollama running:

```sh
cd /home/sean/projects/edgeloop-ai-fork
EDGELOOP_OLLAMA_URL=http://127.0.0.1:11435 ./tools/serve-ai.sh
```

If the existing observer uses a custom `EDGELOOP_FORK_AI_DATA`, preserve that value. Reload the EdgeLoop browser UI, pair with the updated observer through the existing local pairing flow, open Session Journal, then enable recording and optionally historical AI access. No record is created merely by upgrading.

```sh
.venv/bin/python tools/fork_validate.py --tests --report /tmp/f284-upstream.json
.venv/bin/python -m pytest -q tests/ai tests/fork
node --test --test-isolation=none --test-reporter=tap tests/fork/*.test.mjs
node tests/fork/session-journal-browser.mjs
.venv/bin/python -m tests.fork.session_journal_evaluation --live --output /tmp/f284-evaluation.json
```

Implementation commits: `ae6f946`, `38883be`, `a0b3053`, followed by the final validation/documentation commit. Final checkpoint tag: **`f2.8.4-checkpoint`**. Resolve its exact commit with `git rev-parse f2.8.4-checkpoint`.
