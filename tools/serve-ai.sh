#!/usr/bin/env bash
# AGPL-3.0-only. Reuse existing AI modules/dependencies; no session controller.
set -euo pipefail
fork_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
ai_source=${EDGELOOP_AI_SOURCE:-/home/sean/projects/edgeloop-ai}
export PYTHONPATH="$fork_root:$ai_source${PYTHONPATH:+:$PYTHONPATH}"
exec "$ai_source/.venv/bin/python" -m ai_observer.server
