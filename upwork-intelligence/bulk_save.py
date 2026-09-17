#!/usr/bin/env python3
"""Write slim MCP search batches into mcp_raw/*.json"""
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
    client = {}
    for key in ("country", "verification_status", "total_spent", "rating", "total_posted_jobs", "total_reviews"):
        if c.get(key) is not None:
            client[key] = c[key]
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


def slim_resp(r: dict) -> dict:
    if r.get("error"):
        return {"status": "error", "jobs": [], "error": r.get("error")}
    jobs = [slim_job(j) for j in (r.get("jobs") or [])]
    return {"status": r.get("status", "ok"), "jobs": jobs}


def main() -> None:
    path = Path(sys.argv[1])
    batch = json.loads(path.read_text())
    if isinstance(batch, dict):
        batch = [batch]
    for item in batch:
        kw = item["keyword"]
        resp = item.get("response") or item
        if "jobs" not in resp and item.get("error"):
            resp = {"status": "error", "jobs": [], "error": item["error"]}
        entry = {
            "keyword": kw,
            "group": groups.get(kw, item.get("group", "UNKNOWN")),
            "response": slim_resp(resp),
        }
        if item.get("error"):
            entry["error"] = item["error"]
        (RAW / f"{slug(kw)}.json").write_text(json.dumps(entry, ensure_ascii=False))
    print(f"saved {len(batch)} keywords to mcp_raw")


if __name__ == "__main__":
    main()
