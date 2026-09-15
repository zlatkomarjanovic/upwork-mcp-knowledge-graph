#!/usr/bin/env python3
"""Record batch file: {"entries":[{"keyword":"...","jobs":[...]}, ...]}"""
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

path = Path(__file__).parent / "_search_batches.jsonl"
data = json.load(open(sys.argv[1]))
with path.open("a") as f:
    for e in data.get("entries", []):
        jobs = [slim_job(j) for j in e.get("jobs", [])]
        f.write(json.dumps({"keyword": e["keyword"], "jobs": jobs}) + "\n")
print("recorded", len(data.get("entries", [])))
