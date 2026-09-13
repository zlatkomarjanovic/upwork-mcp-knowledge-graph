#!/usr/bin/env python3
"""Append one keyword result to run-results.jsonl. Args: KEYWORD GROUP path/to/mcp.json"""
import json
import sys
from pathlib import Path

kw, group, path = sys.argv[1], sys.argv[2], sys.argv[3]
resp = json.loads(Path(path).read_text())
jobs = resp.get("jobs") or []
line = json.dumps({"keyword": kw, "group": group, "jobs": jobs}, separators=(",", ":"))
Path(__file__).parent.joinpath("run-results.jsonl").open("a").write(line + "\n")
