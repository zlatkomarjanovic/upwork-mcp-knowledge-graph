#!/usr/bin/env python3
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
raw_path = BASE / "_raw_run.json"
raw = json.loads(raw_path.read_text())
batch = json.loads(sys.stdin.read())
if isinstance(batch, dict) and "keyword" in batch:
    batch = [batch]
for item in batch:
    raw["searches"].append(item)
raw["meta"]["keywordsCompleted"] = len(raw["searches"])
raw_path.write_text(json.dumps(raw))
print(len(raw["searches"]))
