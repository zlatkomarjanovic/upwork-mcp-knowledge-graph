#!/usr/bin/env bash
# Agent must run Upwork MCP searches; this script only processes mcp_cache afterward.
set -euo pipefail
cd "$(dirname "$0")"
python3 merge_mcp_cache.py
python3 fill_missing_batches.py
python3 process_run.py
