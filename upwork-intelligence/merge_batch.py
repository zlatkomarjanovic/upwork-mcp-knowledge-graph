#!/usr/bin/env python3
"""Merge batch JSON files into _run_raw.json. Usage: merge_batch.py file1.json [file2.json ...]"""
import json
import sys
from pathlib import Path

BASE = Path(__file__).parent
OUT = BASE / "_run_raw.json"
data = {"searches": {}, "errors": []}
if OUT.exists():
    data = json.loads(OUT.read_text())
for path in sys.argv[1:]:
    chunk = json.loads(Path(path).read_text())
    for k, v in chunk.get("searches", {}).items():
        data["searches"][k] = v
    for e in chunk.get("errors", []):
        if e not in data["errors"]:
            data["errors"].append(e)
OUT.write_text(json.dumps(data))
