#!/usr/bin/env python3
"""Merge MCP batch file into search-results-raw.json. Batch: [{keyword, group, response}] or {error:true}."""
import json
import sys
from pathlib import Path

BASE = Path(__file__).parent
RAW = BASE / "search-results-raw.json"
batch = json.loads(Path(sys.argv[1]).read_text())
data = json.loads(RAW.read_text())
by_kw = {s["keyword"]: i for i, s in enumerate(data["searches"])}

KEYS = (
    "url", "title", "description_snippet", "published_date", "created_date",
    "job_type", "budget", "duration", "proposal_count", "client",
    "experience_level", "skills",
)


def slim(j):
    return {k: j[k] for k in KEYS if k in j}


for item in batch:
    kw = item["keyword"]
    group = item["group"]
    resp = item.get("response") or {}
    idx = by_kw.get(kw)
    if resp.get("status") == "ok":
        entry = {"keyword": kw, "group": group, "jobs": [slim(j) for j in resp.get("jobs", [])]}
        if idx is not None:
            data["searches"][idx] = entry
        else:
            data["searches"].append(entry)
            by_kw[kw] = len(data["searches"]) - 1
        if kw in data.get("errors", []):
            data["errors"] = [e for e in data["errors"] if e != kw]
    elif item.get("error") or resp.get("status") == "error":
        entry = {"keyword": kw, "group": group, "error": True}
        if idx is not None:
            data["searches"][idx] = entry
        if kw not in data.setdefault("errors", []):
            data["errors"].append(kw)

RAW.write_text(json.dumps(data))
ok = sum(1 for s in data["searches"] if not s.get("error"))
print(json.dumps({"completed": ok, "total": len(data["searches"])}))
