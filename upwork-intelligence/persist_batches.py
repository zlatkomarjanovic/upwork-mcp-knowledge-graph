#!/usr/bin/env python3
"""Append batch lines from JSON file (list of {keyword, jobs?, error?}) to _search_batches.jsonl"""
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
BATCH = BASE / "_search_batches.jsonl"
CACHE = BASE / "mcp_cache"
CACHE.mkdir(exist_ok=True)

path = sys.argv[1] if len(sys.argv) > 1 else None
if path:
    data = json.loads(Path(path).read_text())
else:
    data = json.load(sys.stdin)
if isinstance(data, dict):
    data = [data]
n = 0
with BATCH.open("a") as f:
    for rec in data:
        kw = rec["keyword"]
        jobs = rec.get("jobs", [])
        err = rec.get("error")
        safe = str(abs(hash(kw)))
        (CACHE / f"{safe}.json").write_text(
            json.dumps({"keyword": kw, "jobs": jobs}, ensure_ascii=False)
        )
        f.write(json.dumps({"keyword": kw, "jobs": jobs, "error": err}, ensure_ascii=False) + "\n")
        n += 1
print(n)
