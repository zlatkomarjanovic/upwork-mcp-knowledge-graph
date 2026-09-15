#!/usr/bin/env python3
"""Append one keyword batch line from JSON on stdin: {"keyword":"...", "jobs":[...]}"""
import json
import sys
from pathlib import Path

BATCH = Path(__file__).resolve().parent / "_search_batches.jsonl"
data = json.load(sys.stdin)
line = json.dumps({"keyword": data["keyword"], "jobs": data.get("jobs", [])}, ensure_ascii=False)
with BATCH.open("a") as f:
    f.write(line + "\n")
