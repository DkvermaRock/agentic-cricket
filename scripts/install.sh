#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
export UV_CACHE_DIR="${UV_CACHE_DIR:-/workspace/.cache/uv}"
uv sync --locked
npm --prefix frontend ci --no-audit --no-fund --cache /workspace/.cache/npm
npm --prefix frontend run build
