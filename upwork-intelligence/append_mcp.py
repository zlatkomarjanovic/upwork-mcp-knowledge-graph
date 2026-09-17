#!/usr/bin/env python3
"""Append {keyword, response|error} rows to _batch_results.jsonl. Usage: append_mcp.py file.json [file2...]"""
import json, sys
from pathlib import Path

OUT = Path(__file__).parent / "_batch_results.jsonl"

def strip_job(j):
    c = j.get("client") or {}
    return {
        "url": j.get("url"),
        "title": j.get("title"),
        "published_date": j.get("published_date"),
        "created_date": j.get("created_date"),
        "job_type": j.get("job_type"),
        "budget": j.get("budget"),
        "duration": j.get("duration"),
        "proposals_tier": j.get("proposals_tier"),
        "experience_level": j.get("experience_level"),
        "skills": j.get("skills"),
        "client": {
            "country": c.get("country"),
            "verification_status": c.get("verification_status"),
            "total_spent": c.get("total_spent"),
            "rating": c.get("rating"),
        },
    }

def normalize_row(row):
    if "error" in row:
        return {"keyword": row["keyword"], "error": row["error"]}
    mcp = row.get("response") or row.get("mcp") or row
    jobs = mcp.get("jobs") if isinstance(mcp, dict) else None
    if jobs is None and isinstance(row.get("jobs"), list):
        jobs = row["jobs"]
    if jobs is None:
        return {"keyword": row["keyword"], "error": "no jobs in payload"}
    return {"keyword": row["keyword"], "response": {"jobs": [strip_job(j) for j in jobs]}}

def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("a", encoding="utf-8") as out:
        for path in sys.argv[1:]:
            data = json.loads(Path(path).read_text())
            rows = data if isinstance(data, list) else [data]
            for row in rows:
                if "keyword" not in row:
                    continue
                out.write(json.dumps(normalize_row(row), ensure_ascii=False) + "\n")

if __name__ == "__main__":
    main()
