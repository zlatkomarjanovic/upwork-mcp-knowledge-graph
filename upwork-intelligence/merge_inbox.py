#!/usr/bin/env python3
"""Merge inbox/*.json into search_responses.json ordered by keywords.json."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
keywords = json.loads((ROOT / "keywords.json").read_text())
inbox = ROOT / "inbox"
by_kw = {}
if inbox.is_dir():
    for p in inbox.glob("*.json"):
        e = json.loads(p.read_text())
        by_kw[e["keyword"]] = e
out = []
for k in keywords:
    kw = k["keyword"]
    if kw in by_kw:
        out.append(by_kw[kw])
    else:
        out.append({"keyword": kw, "group": k["group"], "jobs": [], "error": "not_fetched"})
(ROOT / "search_responses.json").write_text(json.dumps(out, ensure_ascii=False))
print(json.dumps({"entries": len(out), "with_jobs": sum(1 for e in out if e.get("jobs"))}))
