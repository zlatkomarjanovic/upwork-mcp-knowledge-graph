#!/usr/bin/env python3
"""Merge raw_batches/*.json into search-raw.json for process-run.mjs."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
KEYWORDS = json.loads((ROOT / "keywords.json").read_text())
BATCH_DIR = ROOT / "raw_batches"
BATCH_DIR.mkdir(exist_ok=True)

searches = []
errors = []
done = set()

for p in sorted(BATCH_DIR.glob("*.json")):
    data = json.loads(p.read_text())
    kw = data.get("keyword")
    if not kw:
        continue
    done.add(kw)
    searches.append(
        {
            "keyword": kw,
            "group": data.get("group"),
            "jobs": data.get("jobs", []),
        }
    )

for item in KEYWORDS:
    kw = item["keyword"]
    if kw not in done:
        errors.append(kw)

out = {"searches": searches, "errors": errors}
(ROOT / "search-raw.json").write_text(json.dumps(out))
print(json.dumps({"searches": len(searches), "errors": len(errors)}, indent=2))
