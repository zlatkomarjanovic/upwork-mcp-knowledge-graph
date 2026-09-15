#!/usr/bin/env python3
"""Print keyword batches not yet in queue (for manual MCP runs)."""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
keywords = json.loads((BASE / "keywords.json").read_text())
done = set()
q = BASE / "_search_queue.jsonl"
if q.exists():
    for line in q.read_text().splitlines():
        if line.strip():
            done.add(json.loads(line)["keyword"])
remaining = [(k["keyword"], k["group"]) for k in keywords if k["keyword"] not in done]
for i in range(0, len(remaining), 6):
    batch = remaining[i : i + 6]
    print("BATCH", i // 6 + 1, ":", ", ".join(b[0] for b in batch))
