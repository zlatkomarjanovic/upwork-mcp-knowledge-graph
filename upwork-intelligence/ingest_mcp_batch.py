#!/usr/bin/env python3
"""Ingest agent MCP batch: JSON array of {keyword, group, response} -> raw_batches + search_results.jsonl"""
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
    "proposal_count", "proposals_tier", "duration", "experience_level", "skills", "id",
    "engagement", "featured",
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
    items = json.load(sys.stdin)
    if not isinstance(items, list):
        items = [items]
    for item in items:
        kw = item.get("keyword")
        group = item.get("group")
        resp = item.get("response") or item
        if not kw or not group:
            continue
        payload = {
            "keyword": kw,
            "group": group,
            "response": {
                "status": resp.get("status", "ok"),
                "jobs": [compact_job(j) for j in (resp.get("jobs") or [])],
            },
        }
        if payload["response"]["status"] != "ok":
            payload["error"] = True
        slug = hashlib.md5(kw.encode()).hexdigest()[:12]
        (RAW / f"{slug}.json").write_text(json.dumps(payload, ensure_ascii=False))
        with OUT.open("a") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
        print(kw, payload["response"]["status"], len(payload["response"]["jobs"]))


if __name__ == "__main__":
    main()
