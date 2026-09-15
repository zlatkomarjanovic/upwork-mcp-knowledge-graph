#!/usr/bin/env python3
"""Merge mcp_cache/*.json (array or {keyword,jobs}) into _search_batches.jsonl"""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
CACHE = BASE / "mcp_cache"
BATCH = BASE / "_search_batches.jsonl"
CACHE.mkdir(exist_ok=True)

lines = []
for path in sorted(CACHE.glob("*.json")):
    data = json.loads(path.read_text())
    if isinstance(data, list):
        for rec in data:
            lines.append({"keyword": rec["keyword"], "jobs": rec.get("jobs", [])})
    else:
        lines.append({"keyword": data["keyword"], "jobs": data.get("jobs", [])})

with BATCH.open("w") as f:
    for rec in lines:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
print(len(lines), "keywords merged")
