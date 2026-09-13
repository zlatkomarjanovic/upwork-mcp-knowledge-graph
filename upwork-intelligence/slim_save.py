#!/usr/bin/env python3
"""Read batch JSON from stdin and write search_batch_NNN.json with slim job payloads."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
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
    batch = int(sys.argv[1])
    entries = json.loads(sys.stdin.read())
    slimmed = []
    for e in entries:
        slimmed.append(
            {
                "keyword": e["keyword"],
                "group": e["group"],
                "response": slim_response(e.get("response") or {}),
            }
        )
    out = ROOT / f"search_batch_{batch:03d}.json"
    out.write_text(json.dumps(slimmed, ensure_ascii=False))


if __name__ == "__main__":
    main()
