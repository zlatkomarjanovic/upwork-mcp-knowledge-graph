#!/usr/bin/env python3
"""Append one search from MCP JSON file: python3 _strip_and_append.py KEYWORD GROUP response.json"""
import json
import sys
from pathlib import Path

FIELDS = (
    "url", "title", "published_date", "created_date", "job_type", "budget",
    "duration", "proposal_count", "experience_level", "skills", "description_snippet",
)
path = Path(__file__).parent / "search-results-raw.json"
data = json.loads(path.read_text())
resp = json.loads(Path(sys.argv[3]).read_text())
jobs = []
for j in resp.get("jobs") or []:
    jobs.append({k: j.get(k) for k in FIELDS} | {"client": j.get("client")})
entry = {"keyword": sys.argv[1], "group": sys.argv[2], "jobs": jobs}
if resp.get("status") != "ok":
    entry["error"] = True
data["searches"].append(entry)
path.write_text(json.dumps(data))
