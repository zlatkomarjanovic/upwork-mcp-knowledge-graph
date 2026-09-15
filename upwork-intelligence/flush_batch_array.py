#!/usr/bin/env python3
"""Append [{keyword, jobs}, ...] from JSON file to _search_batches.jsonl"""
import json
import sys
from pathlib import Path

BATCH = Path(__file__).resolve().parent / "_search_batches.jsonl"
path = Path(sys.argv[1])
data = json.loads(path.read_text())
if isinstance(data, dict):
    data = [data]
with BATCH.open("a") as f:
    for rec in data:
        f.write(
            json.dumps(
                {"keyword": rec["keyword"], "jobs": rec.get("jobs", [])},
                ensure_ascii=False,
            )
            + "\n"
        )
print(len(data), "lines appended")
