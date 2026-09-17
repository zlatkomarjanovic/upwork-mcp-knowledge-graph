#!/usr/bin/env python3
"""Save one Upwork find_jobs response: store_mcp_result.py KEYWORD < response.json"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "mcp_raw"
RAW.mkdir(exist_ok=True)
groups = {k["keyword"]: k["group"] for k in json.loads((ROOT / "keywords.json").read_text())}


def slug(kw: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", kw.lower()).strip("_")


def slim_job(j: dict) -> dict:
    c = j.get("client") or {}
    client = {k: c[k] for k in ("country", "verification_status", "total_spent", "rating", "total_posted_jobs", "total_reviews") if c.get(k) is not None}
    out = {
        "url": j.get("url"),
        "title": j.get("title"),
        "published_date": j.get("published_date"),
        "created_date": j.get("created_date"),
        "job_type": j.get("job_type"),
        "budget": j.get("budget"),
        "duration": j.get("duration"),
        "proposal_count": j.get("proposal_count"),
        "proposals_tier": j.get("proposals_tier"),
        "experience_level": j.get("experience_level"),
        "skills": j.get("skills"),
    }
    if client:
        out["client"] = client
    return out


def main() -> None:
    kw = sys.argv[1]
    resp = json.load(sys.stdin)
    jobs = [slim_job(j) for j in (resp.get("jobs") or [])]
    entry = {
        "keyword": kw,
        "group": groups.get(kw, "UNKNOWN"),
        "response": {"status": resp.get("status", "ok"), "jobs": jobs},
    }
    if resp.get("error"):
        entry["error"] = resp["error"]
    (RAW / f"{slug(kw)}.json").write_text(json.dumps(entry, ensure_ascii=False))


if __name__ == "__main__":
    main()
