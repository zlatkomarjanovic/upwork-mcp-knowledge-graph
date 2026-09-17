#!/usr/bin/env python3
"""One-shot: write cache/*.json from search_responses.json."""
import json
from pathlib import Path
from urllib.parse import quote

from save_batch import slim

ROOT = Path(__file__).parent
CACHE = ROOT / "cache"
CACHE.mkdir(exist_ok=True)
data = json.loads((ROOT / "search_responses.json").read_text())
for entry in data:
    kw = entry["keyword"]
    resp = slim(entry.get("response") or {"status": "error", "jobs": []})
    (CACHE / f"{quote(kw, safe='')}.json").write_text(
        json.dumps({"keyword": kw, "response": resp}, ensure_ascii=False)
    )
print(len(data))
