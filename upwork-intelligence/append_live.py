#!/usr/bin/env python3
"""Append one MCP search result to live_mcp.jsonl (stdin: full response JSON, argv[1]=keyword)."""
import json
import sys
from pathlib import Path

LIVE = Path(__file__).parent / "live_mcp.jsonl"
kw = sys.argv[1]
resp = json.loads(sys.stdin.read())
with LIVE.open("a") as f:
    f.write(json.dumps({"keyword": kw, "response": resp}) + "\n")
print(kw)
