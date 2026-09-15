#!/usr/bin/env python3
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
OUT = BASE / "_search_batches.jsonl"
chunks = sorted(BASE.glob("_chunk*.json"))
lines = []
for ch in chunks:
    data = json.loads(ch.read_text())
    for item in data:
        lines.append(json.dumps({"keyword": item["keyword"], "jobs": item.get("jobs", [])}, ensure_ascii=False))
OUT.write_text("\n".join(lines) + ("\n" if lines else ""))
print(len(lines), "batch lines written")
