#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [[ -f mcp-capture.json ]]; then
  node flush-capture.mjs mcp-capture.json
fi
python3 merge-raw.py
RUN_AT="$(date -u +%Y-%m-%dT%H:%M:%S.000Z)"
node process-run.mjs search-raw.json "$RUN_AT"
