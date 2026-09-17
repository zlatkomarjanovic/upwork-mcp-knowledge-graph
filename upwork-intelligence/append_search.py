#!/usr/bin/env python3
"""Append one search result to batch_results.json (stdin: MCP JSON response)."""
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
BATCH = BASE / "batch_results.json"
keyword = sys.argv[1]
group = sys.argv[2]
raw = json.load(sys.stdin)

if BATCH.exists():
    data = json.loads(BATCH.read_text())
else:
    data = {"runNumber": 1, "windowHours": 2, "searches": []}

entry = {"keyword": keyword, "group": group}
def slim(job):
    keep = (
        "url",
        "title",
        "job_type",
        "budget",
        "duration",
        "proposals_tier",
        "published_date",
        "created_date",
        "experience_level",
        "skills",
        "description_snippet",
        "client",
    )
    return {k: job.get(k) for k in keep if k in job}


if raw.get("status") == "ok" and raw.get("jobs") is not None:
    entry["jobs"] = [slim(j) for j in raw["jobs"]]
elif raw.get("error") or raw.get("status") != "ok":
    entry["error"] = raw.get("error") or raw.get("message") or str(raw)[:200]
else:
    entry["jobs"] = raw.get("jobs") or []

data["searches"] = [s for s in data["searches"] if s["keyword"] != keyword]
data["searches"].append(entry)
BATCH.write_text(json.dumps(data, ensure_ascii=False))
