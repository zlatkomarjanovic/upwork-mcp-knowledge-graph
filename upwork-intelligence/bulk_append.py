#!/usr/bin/env python3
"""Append keyword batch records: [{keyword, jobs}, ...] to _search_batches.jsonl"""
import json
import sys
from pathlib import Path

BATCH = Path(__file__).resolve().parent / "_search_batches.jsonl"
data = json.load(sys.stdin)
if not isinstance(data, list):
    data = [data]
with BATCH.open("a") as f:
    for rec in data:
        f.write(json.dumps({"keyword": rec["keyword"], "jobs": rec.get("jobs", [])}, ensure_ascii=False) + "\n")
print(len(data))
