#!/usr/bin/env bash
# Cache-backed Upwork title search for build_cycle_searches.py (cloud agent fills agent/mcp-cache/*.json)
set -euo pipefail
kw="$1"
slug=$(python3 -c "import re; s=re.sub(r'[^a-z0-9]+','_', '''$kw'''.lower()).strip('_'); print(s[:80])")
cache="/workspace/agent/mcp-cache/${slug}.json"
if [[ -f "$cache" ]]; then
  cat "$cache"
  exit 0
fi
echo '{"status":"error","message":"missing mcp cache — run Upwork MCP title search and save cache","jobs":[]}'
exit 1
