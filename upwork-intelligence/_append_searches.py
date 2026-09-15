#!/usr/bin/env python3
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
raw = BASE / "_raw_run.json"
data = json.loads(raw.read_text())
items = json.loads(sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read())
if isinstance(items, dict) and "keyword" in items:
    items = [items]
data["searches"].extend(items)
data["meta"]["keywordsCompleted"] = len(data["searches"])
raw.write_text(json.dumps(data))
print(len(data["searches"]))
