#!/usr/bin/env python3
import json
from pathlib import Path

BASE = Path(__file__).parent
keywords = json.loads((BASE / "keywords.json").read_text())
by_kw = {}
errors = []
batch_path = BASE / "batches.jsonl"
if batch_path.exists():
    for line in batch_path.read_text().splitlines():
        if not line.strip():
            continue
        e = json.loads(line)
        by_kw[e["keyword"]] = e
        if e.get("error"):
            errors.append(e["keyword"])

searches = []
for meta in keywords:
    kw, grp = meta["keyword"], meta["group"]
    if kw in by_kw:
        e = by_kw[kw]
        if e.get("error"):
            searches.append({"keyword": kw, "group": grp, "error": True})
        else:
            searches.append({"keyword": kw, "group": grp, "jobs": e.get("jobs", [])})
    else:
        errors.append(kw)
        searches.append({"keyword": kw, "group": grp, "error": True})

(BASE / "search_responses.json").write_text(json.dumps({"searches": searches, "errors": list(dict.fromkeys(errors))}))
