# Attribution and source

This experimental fork contains EdgeLoop by marshallmims, version 1.1.3,
commit d351e011249079b368ebdc8d46f83b260be7d2a5:
https://github.com/marshallmims/edgeloop

The original application and these fork additions are distributed under
AGPL-3.0-only. The original LICENSE and upstream notices remain intact.
All 85 original pinned files are unchanged at the F1 source checkpoint.
F2 adds optional read-only AI UI/telemetry, an observer-only service, tests and
private-data isolation. The engine, session handlers, calculations and drivers
remain unchanged; the reviewed original-file changes are recorded separately.

Retain source access and this attribution if the fork is distributed or made
available over a network. The Git repository and provenance manifest identify
the exact corresponding source. User data, device keys, model weights and
conversation records are not part of this source checkout.

The pre-existing EdgeLoop AI application remains a separate project. Its AI
provider, model manager, conversation service, Director and memory implementation
are imported here from checkpoint 9e89fa1 without copying or replacing them.
The corresponding AI source remains at /home/sean/projects/edgeloop-ai/ under
AGPL-3.0-only; provide both source repositories when distributing this extension.
