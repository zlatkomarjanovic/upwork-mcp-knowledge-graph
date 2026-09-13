#!/usr/bin/env python3
"""Append one keyword search result to _run_raw.json. Usage: append_search.py KEYWORD < result.json"""
import json
import sys
from pathlib import Path

BASE = Path(__file__).parent
OUT = BASE / "_run_raw.json"
kw = sys.argv[1]
result = json.load(sys.stdin)
data = {"searches": {}, "errors": []}
if OUT.exists():
    data = json.loads(OUT.read_text())
if result.get("status") == "error":
    if kw not in data["errors"]:
        data["errors"].append(kw)
else:
    data["searches"][kw] = result
OUT.write_text(json.dumps(data))
