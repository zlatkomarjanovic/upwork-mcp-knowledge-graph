#!/usr/bin/env python3
"""Append keyword batch records from JSON array on stdin to mcp_cache and _search_batches.jsonl"""
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
CACHE = BASE / "mcp_cache"
BATCH = BASE / "_search_batches.jsonl"
CACHE.mkdir(exist_ok=True)

data = json.load(sys.stdin)
if isinstance(data, dict):
    data = [data]

for rec in data:
    kw = rec["keyword"]
    safe = str(abs(hash(kw)))
    (CACHE / f"{safe}.json").write_text(
        json.dumps({"keyword": kw, "jobs": rec.get("jobs", [])}, ensure_ascii=False)
    )
    with BATCH.open("a") as f:
        f.write(
            json.dumps(
                {"keyword": kw, "jobs": rec.get("jobs", []), "error": rec.get("error")},
                ensure_ascii=False,
            )
            + "\n"
        )
print(len(data))
