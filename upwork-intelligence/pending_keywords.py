#!/usr/bin/env python3
import json
from pathlib import Path
ROOT = Path(__file__).parent
keywords = json.loads((ROOT / "keywords.json").read_text())
done = set()
batch = ROOT / "_search_batches.jsonl"
if batch.exists():
    for line in batch.read_text().splitlines():
        if line.strip():
            done.add(json.loads(line)["keyword"])
pending = [k for k in keywords if k not in done]
print(json.dumps(pending))
