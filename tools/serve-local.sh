#!/usr/bin/env bash
# AGPL-3.0-only. Manual localhost-only development server; no services/devices.
set -euo pipefail
fork_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
exec python3 -m http.server "${1:-8770}" --bind 127.0.0.1 --directory "$fork_root"
