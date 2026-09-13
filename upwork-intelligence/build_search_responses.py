#!/usr/bin/env python3
import json
from pathlib import Path

BASE = Path(__file__).parent
meta = json.loads((BASE / "keywords.json").read_text())
by_kw = {}
for line in (BASE / "batches.jsonl").read_text().splitlines():
    if line.strip():
        e = json.loads(line)
        by_kw[e["keyword"]] = e

searches, errors = [], []
for m in meta:
    kw, grp = m["keyword"], m["group"]
    if kw in by_kw and not by_kw[kw].get("error"):
        searches.append({"keyword": kw, "group": grp, "jobs": by_kw[kw].get("jobs", [])})
    else:
        searches.append({"keyword": kw, "group": grp, "error": True})
        errors.append(kw)

(BASE / "search_responses.json").write_text(json.dumps({"searches": searches, "errors": errors}))
