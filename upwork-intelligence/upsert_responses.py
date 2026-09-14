#!/usr/bin/env python3
"""Merge batch updates into search_responses.json (stdin: JSON array of entries)."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
keywords = json.loads((ROOT / "keywords.json").read_text())
updates = json.load(sys.stdin)
by_kw = {}
path = ROOT / "search_responses.json"
if path.exists():
    for e in json.loads(path.read_text()):
        by_kw[e["keyword"]] = e
for u in updates:
    entry = {
        "keyword": u["keyword"],
        "group": u["group"],
        "response": u.get("response") or {"jobs": u.get("jobs") or [], "status": "ok"},
    }
    if u.get("error"):
        entry["error"] = u["error"]
    by_kw[u["keyword"]] = entry
out = [by_kw.get(k["keyword"], {"keyword": k["keyword"], "group": k["group"], "response": {"jobs": []}, "error": "not_fetched"}) for k in keywords]
path.write_text(json.dumps(out, ensure_ascii=False))
print(json.dumps({"updated": len(updates), "total": len(out)}))
