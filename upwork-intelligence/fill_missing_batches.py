#!/usr/bin/env python3
"""Ensure _search_batches.jsonl has one line per keyword; missing keywords get error:true."""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys_path = BASE / "process_run.py"
import importlib.util

spec = importlib.util.spec_from_file_location("process_run", BASE / "process_run.py")
pr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pr)
ALL_KEYWORDS = pr.ALL_KEYWORDS
BATCH = BASE / "_search_batches.jsonl"

done = {}
if BATCH.exists():
    for line in BATCH.read_text().splitlines():
        if line.strip():
            o = json.loads(line)
            done[o["keyword"]] = o

with BATCH.open("w") as f:
    for kw in ALL_KEYWORDS:
        if kw in done:
            f.write(json.dumps(done[kw], ensure_ascii=False) + "\n")
        else:
            f.write(json.dumps({"keyword": kw, "jobs": [], "error": True}, ensure_ascii=False) + "\n")
print("filled", len(ALL_KEYWORDS), "lines, had", len(done))
