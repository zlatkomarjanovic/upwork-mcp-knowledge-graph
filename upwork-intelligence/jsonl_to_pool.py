#!/usr/bin/env python3
"""Convert jobs.jsonl records to fresh_jobs_pool MCP-shaped jobs."""
import json
from pathlib import Path

BASE = Path(__file__).parent
JOBS = BASE / "jobs.jsonl"
POOL = BASE / "fresh_jobs_pool.json"

def to_pool_job(j):
    return {
        "url": j.get("url"),
        "title": j.get("title"),
        "published_date": j.get("postedAt"),
        "created_date": j.get("postedAt"),
        "job_type": j.get("type"),
        "budget": j.get("budget"),
        "duration": j.get("duration"),
        "proposals_tier": j.get("proposals") if isinstance(j.get("proposals"), str) else None,
        "experience_level": j.get("experienceLevel"),
        "skills": j.get("skills"),
        "client": {
            "country": j.get("clientCountry"),
            "verification_status": "VERIFIED" if j.get("paymentVerified") else None,
            "total_spent": j.get("clientSpend"),
            "rating": j.get("clientRating"),
        },
    }

def main():
    pool = []
    seen = set()
    if JOBS.exists():
        for line in JOBS.read_text().splitlines():
            if not line.strip():
                continue
            j = json.loads(line)
            u = (j.get("url") or "").split("?")[0]
            if u and u not in seen:
                seen.add(u)
                pool.append(to_pool_job(j))
    POOL.write_text(json.dumps(pool, ensure_ascii=False, indent=2))
    print(len(pool))

if __name__ == "__main__":
    main()
