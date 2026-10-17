#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
test -f frontend/dist/index.html || { echo 'Run bash scripts/install.sh first.' >&2; exit 1; }
exec .venv/bin/python -m backend
