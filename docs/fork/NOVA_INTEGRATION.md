# Nova integration

Nova uses the existing character contract under the exact model name `nova-narrative-v1:latest`.

- Persona source: `characters/models/nova-narrative-v1/Modelfile`, preserved unchanged. The native Ollama SYSTEM remains authoritative for her identity; no competing runtime personality was added.
- Artwork: `Character_Art/Nova/expressions/`, referenced directly without resizing, renaming or copying. All 12 supplied expression images are registered. The supplied `nova_dissapointed.png` spelling is intentional in the path mapping. The supplied `nova_excited.png` is mapped directly to the excited expression; neutral fallback remains available if an asset fails to load. `nova_reference.png` remains outside the public asset allowlist.
- Chat identity, portrait, local preview, expression protocol and model switching use the shared manifest. Unknown Nova-like model aliases still receive the generic placeholder.
- Event relevance defaults are neutral and migrate old configurations without changing existing character settings. The UI only builds relevance controls supported by the connected observer, keeping a new page compatible with an older running observer until activation/reload.
- Story Memory remains scoped by the selected model and narrative epoch. Session Journal recognizes explicit Nova requests and preserves its recording/access privacy controls. No fictional memory is promoted to verified session data.
- Native model/source files, existing model installations, artwork, conversation data, original hardware/safety pathways and prior uncommitted memory work were preserved. Ordinary inference still sends `think: false`. No service was restarted and no model was automatically rebuilt or selected.

## Activate when ready

Load the updated observer using your normal launcher when convenient, then reload the UI. No restart was performed during integration.

The model list is discovered from the existing Ollama endpoint, not populated with fictitious installed models. If `nova-narrative-v1:latest` is already installed, select it in Chat. If it is absent, create this new model from the supplied source:

```sh
cd /home/sean/projects/edgeloop-ai-fork
OLLAMA_HOST=127.0.0.1:11435 ollama create nova-narrative-v1 -f characters/models/nova-narrative-v1/Modelfile
```

Do not rebuild an existing Nova installation unnecessarily. Refresh the model list and select Nova after installation. Her 9B base and supplied sampling parameters were not changed. Existing application sampling overrides continue to behave as before.

## Validation

Deterministic coverage verifies asset allowlisting and fallback, exact identity mapping, native SYSTEM preservation, `think: false`, expression switching, old event-configuration migration, compatibility with an older running observer, separate persisted story memory/reset and opt-in historical Nova retrieval.

Results: **663 Python tests passed** (three known socket-dependent cases deselected in this restricted environment), **63 JavaScript tests passed**, and the original-file pin verification passed. Python asynchronous tests used the same test-process-only selector polling shim described in the F2.8.4.2 report; no production asyncio behavior was changed. Source whitespace and browser-runner syntax checks pass. Full logs: `/tmp/nova-python-full.log`, `/tmp/nova-js.log`; pin report: `/tmp/nova-original-files.json`.

The character browser workflow now includes Nova selection, isolated history, expressions, desktop/mobile portraits and all supplied expression assets, including the supplied excited portrait. Repeat it with:

```sh
CHARACTER_BROWSER_REPORT=/tmp/nova-browser node tests/fork/character-browser.mjs
```

The attempted browser run in this environment could not start its isolated fixture (`Fixture did not start`); no rendered-browser acceptance is claimed. The Ollama discovery request separately failed with `Operation not permitted`, so installed-model availability and a live Nova response could not be verified. The supplied neutral portrait was inspected locally. Reports are in `/tmp/nova-browser/` and `/tmp/nova-browser.log`. No user service was affected by test-owned process cleanup.
