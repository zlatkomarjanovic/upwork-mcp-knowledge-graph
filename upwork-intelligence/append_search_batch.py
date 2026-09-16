#!/usr/bin/env python3
"""Append one keyword search result to _search_batches.jsonl (stdin JSON)."""
import json
import sys
from pathlib import Path

BATCH = Path(__file__).resolve().parent / "_search_batches.jsonl"
payload = json.load(sys.stdin)
line = {
    "keyword": payload["keyword"],
    "jobs": payload.get("jobs") or [],
    "error": payload.get("error"),
}
with BATCH.open("a", encoding="utf-8") as f:
    f.write(json.dumps(line, ensure_ascii=False) + "\n")
