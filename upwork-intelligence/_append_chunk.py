#!/usr/bin/env python3
"""Append one search result line to _search_chunks.jsonl (stdin JSON)."""
import json
import sys
from pathlib import Path

BASE = Path(__file__).parent
CHUNKS = BASE / "_search_chunks.jsonl"
rec = json.load(sys.stdin)
rec.setdefault("runAt", "2026-09-15T03:33:28.109Z")
rec.setdefault("runNumber", 1)
with CHUNKS.open("a") as f:
    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
