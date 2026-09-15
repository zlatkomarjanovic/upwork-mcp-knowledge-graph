#!/usr/bin/env python3
"""
Run all keyword searches via Upwork MCP and append to _search_batches.jsonl.

Requires UPWORK_MCP_RUN=1 and a JSON lines file on stdin where each line is:
  {"keyword": "...", "response": {"jobs": [...]}}

Or pass --from-dir mcp_cache/ with per-keyword JSON files.

This script is invoked by the hourly agent after MCP searches complete.
"""
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
from process_run import ALL_KEYWORDS  # noqa: E402

BATCH = BASE / "_search_batches.jsonl"


def strip_job(j):
    c = j.get("client") or {}
    return {
        "url": j.get("url"),
        "title": j.get("title"),
        "description_snippet": j.get("description_snippet") or "",
        "published_date": j.get("published_date"),
        "created_date": j.get("created_date"),
        "job_type": j.get("job_type"),
        "budget": j.get("budget"),
        "duration": j.get("duration"),
        "proposal_count": j.get("proposal_count"),
        "experience_level": j.get("experience_level"),
        "skills": j.get("skills"),
        "client": {
            k: c.get(k)
            for k in (
                "country",
                "verification_status",
                "total_spent",
                "rating",
                "total_posted_jobs",
                "total_reviews",
            )
        },
    }


def append_batch(keyword, jobs, error=False):
    rec = {"keyword": keyword, "jobs": jobs}
    if error:
        rec["error"] = True
    with BATCH.open("a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--from-dir":
        d = Path(sys.argv[2])
        for kw in ALL_KEYWORDS:
            safe = str(abs(hash(kw)))
            path = d / f"{safe}.json"
            if not path.exists():
                for p in d.glob("*.json"):
                    data = json.loads(p.read_text())
                    if data.get("keyword") == kw:
                        path = p
                        break
            if not path.exists():
                append_batch(kw, [], error=True)
                continue
            data = json.loads(path.read_text())
            jobs = [strip_job(j) for j in data.get("jobs", [])]
            append_batch(kw, jobs)
        print("done from dir")
        return

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        kw = row["keyword"]
        resp = row.get("response") or row
        if row.get("error") or resp.get("status") == "error":
            append_batch(kw, [], error=True)
            continue
        jobs = [strip_job(j) for j in resp.get("jobs", [])]
        append_batch(kw, jobs)


if __name__ == "__main__":
    main()
