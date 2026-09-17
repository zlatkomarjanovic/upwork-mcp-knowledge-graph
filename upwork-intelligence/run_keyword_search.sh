#!/usr/bin/env bash
# Usage: agent saves MCP JSON to /tmp/upwork-batch.json then:
#   bash run_keyword_search.sh /tmp/upwork-batch.json
set -euo pipefail
cd "$(dirname "$0")"
python3 save_batch.py "$1"
