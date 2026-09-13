#!/usr/bin/env python3
"""Append slim keyword search entries to search_log.jsonl."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LOG = ROOT / "search_log.jsonl"
JOB_FIELDS = (
    "id",
    "title",
    "url",
    "job_type",
    "budget",
    "duration",
    "experience_level",
    "proposal_count",
    "published_date",
    "created_date",
    "skills",
    "description_snippet",
)
CLIENT_FIELDS = (
    "country",
    "verification_status",
    "total_spent",
    "rating",
    "total_posted_jobs",
    "total_reviews",
)


def slim_response(resp: dict) -> dict:
    if resp.get("status") != "ok":
        return resp
    jobs = []
    for j in resp.get("jobs") or []:
        client = j.get("client") or {}
        jobs.append(
            {
                **{k: j.get(k) for k in JOB_FIELDS},
                "client": {k: client.get(k) for k in CLIENT_FIELDS},
            }
        )
    return {"status": "ok", "jobs": jobs}


def main() -> None:
    path = Path(sys.argv[1])
    chunk = json.loads(path.read_text())
    with LOG.open("a") as f:
        for entry in chunk:
            row = {
                "keyword": entry["keyword"],
                "group": entry["group"],
                "response": slim_response(entry.get("response") or {}),
            }
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
