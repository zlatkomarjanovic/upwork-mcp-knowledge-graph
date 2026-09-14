#!/usr/bin/env python3
"""Write MCP search results into raw_batches/*.json"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BATCH = ROOT / "raw_batches"
BATCH.mkdir(exist_ok=True)

data = json.loads(Path(sys.argv[1]).read_text())
for item in data:
    kw = item["keyword"]
    slug = re.sub(r"[^a-z0-9]+", "-", kw.lower()).strip("-")[:80]
    payload = {
        "keyword": kw,
        "group": item["group"],
        "jobs": item.get("jobs", []),
    }
    if item.get("error"):
        payload["error"] = item["error"]
    (BATCH / f"{slug}.json").write_text(json.dumps(payload))
print(len(data))
