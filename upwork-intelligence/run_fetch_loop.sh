#!/usr/bin/env bash
# Rate-limited keyword fetch placeholder: MCP searches must be executed by the cloud agent
# via Upwork MCP; this script only merges batch JSON files into _run_raw.json.
set -euo pipefail
cd "$(dirname "$0")"
shopt -s nullglob
files=(batches/*.json)
if ((${#files[@]})); then
  python3 merge_batch.py "${files[@]}"
  echo "Merged ${#files[@]} batch files into _run_raw.json"
else
  echo "No batch files in batches/"
fi
