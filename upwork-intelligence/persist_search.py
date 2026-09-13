#!/usr/bin/env python3
"""Append one MCP search to run-results.jsonl. stdin: full MCP JSON; args: keyword group"""
import json
import sys
from pathlib import Path

kw, group = sys.argv[1], sys.argv[2]
resp = json.load(sys.stdin)
jobs = resp.get("jobs") or []
line = json.dumps({"keyword": kw, "group": group, "jobs": jobs}, separators=(",", ":"))
Path(__file__).parent.joinpath("run-results.jsonl").open("a").write(line + "\n")
