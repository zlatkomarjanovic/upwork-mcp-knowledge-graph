#!/usr/bin/env bash
# Rate-limited keyword fetch helper (MCP calls must be done by the agent).
# This script merges _search_queue.jsonl and runs the processor.
set -euo pipefail
cd "$(dirname "$0")"
python3 _run_hourly.py
