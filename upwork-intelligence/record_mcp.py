#!/usr/bin/env python3
"""Append slim MCP search result: record_mcp.py KEYWORD path/to/response.json"""
import json, sys
from pathlib import Path

def slim_job(j):
    c = j.get("client") or {}
    return {
        "url": j.get("url"),
        "title": j.get("title"),
        "job_type": j.get("job_type"),
        "budget": j.get("budget"),
        "duration": j.get("duration"),
        "proposal_count": j.get("proposal_count"),
        "published_date": j.get("published_date"),
        "created_date": j.get("created_date"),
        "experience_level": j.get("experience_level"),
        "skills": j.get("skills"),
        "description_snippet": j.get("description_snippet"),
        "client": {
            "country": c.get("country"),
            "verification_status": c.get("verification_status"),
            "total_spent": c.get("total_spent"),
            "rating": c.get("rating"),
            "total_posted_jobs": c.get("total_posted_jobs"),
            "total_reviews": c.get("total_reviews"),
        },
    }

kw, src = sys.argv[1], sys.argv[2]
data = json.load(open(src))
jobs = [slim_job(j) for j in data.get("jobs") or []]
out = Path(__file__).parent / "_search_batches.jsonl"
with out.open("a") as f:
    f.write(json.dumps({"keyword": kw, "jobs": jobs}) + "\n")
print(kw, len(jobs))
