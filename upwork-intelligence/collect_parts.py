#!/usr/bin/env python3
import json
from pathlib import Path

BASE = Path(__file__).parent
parts = sorted((BASE / "parts").glob("*.json"))
searches = []
errors = []
for p in parts:
    d = json.loads(p.read_text())
    if d.get("error"):
        errors.append(d["keyword"])
        searches.append({"keyword": d["keyword"], "group": d["group"], "error": True})
    else:
        searches.append({"keyword": d["keyword"], "group": d["group"], "jobs": d.get("jobs", [])})
(BASE / "search_responses.json").write_text(json.dumps({"searches": searches, "errors": errors}, indent=0))
print(len(searches), "searches", len(errors), "errors")
