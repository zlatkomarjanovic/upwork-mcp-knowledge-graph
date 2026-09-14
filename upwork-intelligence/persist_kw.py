#!/usr/bin/env python3
"""Persist one find_jobs response: persist_kw.py KEYWORD GROUP < response.json"""
import hashlib
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
RAW = BASE / "raw_batches"
RAW.mkdir(exist_ok=True)
OUT = BASE / "search_results.jsonl"

KEEP = (
    "url", "title", "published_date", "created_date", "budget", "job_type",
    "proposal_count", "duration", "experience_level", "skills", "id", "engagement", "featured",
)


def compact_job(j):
    out = {k: j.get(k) for k in KEEP if k in j}
    c = j.get("client")
    if c:
        out["client"] = {
            k: c.get(k)
            for k in (
                "country", "rating", "total_posted_jobs", "total_reviews",
                "total_spent", "verification_status",
            )
            if k in c
        }
    return out


def main():
    if len(sys.argv) < 3:
        sys.exit("usage: persist_kw.py KEYWORD GROUP")
    keyword, group = sys.argv[1], sys.argv[2]
    resp = json.load(sys.stdin)
    payload = {
        "keyword": keyword,
        "group": group,
        "response": {
            "status": resp.get("status", "ok"),
            "jobs": [compact_job(j) for j in (resp.get("jobs") or [])],
        },
    }
    if payload["response"]["status"] != "ok":
        payload["error"] = True
    slug = hashlib.md5(keyword.encode()).hexdigest()[:12]
    (RAW / f"{slug}.json").write_text(json.dumps(payload, ensure_ascii=False))
    with OUT.open("a") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    print(keyword, len(payload["response"]["jobs"]))


if __name__ == "__main__":
    main()
