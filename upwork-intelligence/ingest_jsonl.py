#!/usr/bin/env python3
"""Merge search_log.jsonl lines into _run_raw.json"""
import json
from pathlib import Path

BASE = Path(__file__).parent
OUT = BASE / "_run_raw.json"
LOG = BASE / "search_log.jsonl"
data = {"searches": {}, "errors": []}
if OUT.exists():
    data = json.loads(OUT.read_text())
if LOG.exists():
    for line in LOG.read_text().splitlines():
        if not line.strip():
            continue
        o = json.loads(line)
        kw = o["kw"]
        result = o["result"]
        if result.get("status") == "error":
            if kw not in data["errors"]:
                data["errors"].append(kw)
        else:
            data["searches"][kw] = result
OUT.write_text(json.dumps(data))
