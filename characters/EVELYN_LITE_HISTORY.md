# Evelyn Lite experiment

`models/evelyn-lite/Modelfile` is the standalone source of truth. It deliberately
contains one compact personality, shared canon and runtime boundary. It does not
use the existing lore-injection builders: those would duplicate the canon.
Existing source definitions, generated variants, application configuration,
conversation history and default selection are preserved.

Base: `huihui_ai/qwen3.5-abliterated:9b`. Sampling parameters match the existing
`evelyn-qwen35` definition: temperature 0.6, top_p 0.95, top_k 20, context 4096.
The base template and thinking support are inherited; no forced thinking text
or custom template is embedded. System text: 1,959 characters versus 8,103 in
the installed `evelyn-qwen35` (75.8% smaller). Runtime context is still supplied
by the app; the prompt is a character boundary, not a device control mechanism.

## Model store and build

On this machine port 11434 serves the project's `.ollama/models`, which contains
older models. The newer Evelyn variants and requested base are in
`~/.ollama/models`. The experiment uses a separate loopback runtime on 11435.
Do not accidentally rebuild a baseline model or point at the wrong store.

Start manually in a terminal, if 11435 is free:

```bash
cd ~/projects/edgeloop-ai
OLLAMA_HOST=127.0.0.1:11435 OLLAMA_MODELS="$HOME/.ollama/models" \
  OLLAMA_NUM_PARALLEL=1 OLLAMA_MAX_LOADED_MODELS=1 OLLAMA_FLASH_ATTENTION=1 \
  ollama serve
```

Build and inspect in another terminal:

```bash
cd ~/projects/edgeloop-ai
OLLAMA_HOST=127.0.0.1:11435 ollama create evelyn-lite -f models/evelyn-lite/Modelfile
OLLAMA_HOST=127.0.0.1:11435 ollama show evelyn-lite --modelfile
OLLAMA_HOST=127.0.0.1:11435 ollama run evelyn-lite
```

Stop the experimental server with Ctrl+C when finished. No service or startup
configuration was installed. The installed model persists in the store after
server shutdown. The existing app on 11434 will not discover models in this
other store. To try it through the app later, launch a separate app instance
with `EDGELOOP_OLLAMA_URL=http://127.0.0.1:11435` and select `evelyn-lite:latest`;
this experiment does not change the running application's selection or history.

## Repeatable comparison

```bash
cd ~/projects/edgeloop-ai
python tools/compare_evelyn_lite.py --output build/evelyn-lite/comparison-new.json
# Four-cell greeting comparison:
python tools/compare_evelyn_lite.py --cases greeting \
  --output build/evelyn-lite/greeting-new.json
# Bounded CPU smoke test; thinking may exhaust this budget without an answer:
python tools/compare_evelyn_lite.py --cases greeting --num-predict 512 \
  --output build/evelyn-lite/greeting-budget512-new.json
```

Each case starts fresh, except the explicit two-turn continuity case. Both
models run with thinking off and on using identical seed, sampling, 8192 context,
4096 generated-token budget and eight CPU threads. The comparison overrides the
models' 4096 context default equally to leave room for reasoning. It never adds
assistant reasoning to history. Verified runtime context is supplied as a system
message appended to the exact embedded character system text, matching the
application's preservation behavior. User-claimed state is tested separately.

JSON saves exact prompts, visible answers, system text/hash, installed model
metadata, settings, completion reasons, prompt/output counts, durations and
thinking character counts. Raw thinking text is not retained. Partial results
are saved after every turn; incomplete answers and request errors produce a
nonzero exit code. A completion flag proves only that output finished; assess
behavior against each row's manual review rubric. A fixed seed does not promise
identical output across hardware/runtime versions. Output files are never
overwritten. Repeat runs with new paths and `--seed 43` (for example) before drawing
quality conclusions. Use `--thinking off` or `--thinking on` to isolate a mode.

Timing includes loading and prompt evaluation. Model/mode execution is grouped,
so cache and order effects apply. Compare `load_duration`, `prompt_eval_duration`
and `eval_duration` as well as elapsed time. The first run in this environment
used Ollama 0.33.3 with CPU only (`size_vram=0`); it cannot establish RTX 3080
latency. Tests are direct Ollama calls, not end-to-end application acceptance.

API references: [Ollama chat](https://docs.ollama.com/api/chat) and
[Modelfile reference](https://docs.ollama.com/modelfile).

## Live results — 27 October 2026

Installed as `evelyn-lite:latest`; base weight digest and installed SYSTEM match the source. All 14 pre-existing model manifests are preserved; the baseline Modelfile matches the pre-build snapshot. No existing source, app defaults or histories were edited.

The bounded greeting run used seed 42, 8192 context and a 512-token output budget on CPU.

| Model | Thinking | Prompt tokens | Generated tokens | Seconds | Outcome |
| --- | --- | ---: | ---: | ---: | --- |
| evelyn-lite | False | 370 | 56 | 12.441 | Finished |
| evelyn-lite | True | 368 | 512 | 112.636 | Budget cutoff; no visible answer |
| evelyn-qwen35 | False | 1587 | 94 | 59.782 | Finished |
| evelyn-qwen35 | True | 1585 | 512 | 108.456 | Budget cutoff; no visible answer |

These are single observations with loading/cache/order effects, not a speed benchmark. Both thinking runs exhausted 512 tokens entirely on reasoning. This does not show that thinking fails with the default 4096-token budget; the earlier full-budget run was interrupted during its first thinking request and supplies no completed thinking evidence.

The interrupted larger run saved seven complete Lite non-thinking replies across six scenarios. Manual review found identity confusion in the greeting, unwanted research talk during the coffee break, invented details around Cloverfield, acceptance of user claims as verified state, and a failure to respect an explicit stop request. The verified-runtime case correctly reflected supplied readings and lack of a record, but had an unnecessarily mocking tone. The baseline greeting also invented shared conversation history. Lite is experimental and is not recommended as a replacement on these results.

Evidence: `build/evelyn-lite/comparison.json` (partial larger run), `build/evelyn-lite/greeting-budget512.json` (finished four-cell smoke run), `build/evelyn-lite/verification.json`, and `build/evelyn-lite/preserved-manifests.json`. Raw answers and metrics remain available for review. The next iteration should target role stability, tone, explicit stops and the report-versus-runtime boundary, then repeat the same cases at a sufficient thinking budget.

## Revision 2 — prompt delivery and targeted repair

The original `evelyn-lite` remains installed unchanged and is also retained as
`evelyn-lite-v1`. The revised model is `evelyn-lite-candidate`, built from
`models/evelyn-lite-candidate/Modelfile`. Keep these source paths separate until
there is evidence to promote the candidate. No old definitions or model tags
have been removed.

Prompt delivery was checked against the live local runtime. Automatic embedded
SYSTEM and explicitly supplied identical SYSTEM each produced 372 prompt tokens
and the same seeded first token. Replacing SYSTEM with a short probe reduced the
prompt to 32 tokens and changed the reply to READY. Runtime debug logs selected
the `qwen3.5` renderer/parser. The short displayed `{{ .Prompt }}` template is not
evidence of a missing SYSTEM. The installed base config selects a built-in
renderer; the [Ollama 0.33.3 renderer source](https://github.com/ollama/ollama/blob/v0.33.3/model/renderers/qwen35.go)
includes leading system-message handling. This is evidence of correct delivery,
not proof that a model will follow every instruction. The application's identity
preservation tests also passed: 10 tests in `tests/test_model_identity.py`.

Revision 2 adds explicit first-person speaker identity, human rather than machine
speech, a gentle tone, casual-topic guidance, and brief examples distinguishing
user claims from runtime confirmation and respecting explicit stops. All other
sampling parameters and base weights remain the same.

Repeat the revision's checks:

```bash
OLLAMA_HOST=127.0.0.1:11435 ollama create evelyn-lite-candidate \
  -f models/evelyn-lite-candidate/Modelfile
python tools/compare_evelyn_lite.py --models evelyn-lite-candidate --thinking off \
  --output build/evelyn-lite/revision-2/off-repeat.json
python tools/compare_evelyn_lite.py --models evelyn-lite-candidate --thinking on \
  --cases unverified hypothesis_discomfort \
  --output build/evelyn-lite/revision-2/on-repeat.json
```

The runner now streams responses to measure first visible output and report
progress while counting, rather than saving, private thinking. Its default total
inference deadline is 1200 seconds; generation remains capped at 4096 tokens.
Interruptions mark the report interrupted and preserve completed rows.

### Revision 2 results and decision

**Do not promote this candidate.** All seven non-thinking turns completed, but
completion is not behavioral correctness. Speaker identity improved and the stop
request was acknowledged as absolute. Research framing and invented off-screen
details persisted. The supplied-runtime reply omitted paused/stationary state,
and the user-claim test explicitly filed the claims as verified.

Thinking on did produce a complete answer for the unverified-state case within
the 4096-token budget: 3675 generated tokens, 836.396 seconds total, first visible
output at 824.617 seconds. Its answer still treated the claimed record and device
start as confirmed. This is a behavioral failure with a completed answer, not a
budget-cutoff inference. Private thinking text was counted but not retained.
The remaining thinking-on stop test was canceled after that critical failure;
there is no completed thinking-on stop result. CPU measurements do not establish
GPU performance.

The original `evelyn-lite` model and source are retained unchanged; the candidate
is available under its separate name for reproduction. All 15 model manifests
present before the revision are unchanged. No running app selection, history,
service, or hardware settings were changed. The temporary runtime was stopped
when testing ended.

Evidence is saved in `build/evelyn-lite/revision-2/`: `prompt-delivery.json`,
`candidate-off.json`, `candidate-on-boundaries.json` (interrupted after one
completed thinking case), `manual-review.json`, `verification.json`, and
`model-inventory.json`. The latter inventories 17 tags sharing two sets of
weights. No models or old source definitions were deleted.

Before further personality expansion, a useful next diagnostic is the same
compact prompt and failed case on an unmodified Qwen 3.5 base. That would test
whether the behavior follows the abliterated weights rather than prompting
alone. Such a comparison has not been run, and no alternative base was downloaded.
