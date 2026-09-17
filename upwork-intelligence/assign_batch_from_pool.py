#!/usr/bin/env python3
"""Assign pooled fresh jobs to keywords (bootstrap when MCP rows not persisted)."""
import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent
POOL = BASE / "fresh_jobs_pool.json"
KEYWORDS = BASE / "keywords.json"
OUT = BASE / "_batch_results.jsonl"


def norm_job(j):
    return {
        "url": j["url"].split("?")[0],
        "title": j.get("title"),
        "published_date": j.get("published_date"),
        "created_date": j.get("created_date"),
        "job_type": j.get("job_type"),
        "budget": j.get("budget"),
        "duration": j.get("duration"),
        "proposals_tier": j.get("proposals_tier"),
        "experience_level": j.get("experience_level"),
        "skills": j.get("skills") or [],
        "client": j.get("client") or {},
    }


def matches(keyword, job):
    text = " ".join([job.get("title") or "", " ".join(job.get("skills") or [])]).lower()
    kw = keyword.lower().strip()
    if kw in {"ghl"}:
        return "ghl" in text or "gohighlevel" in text or "high level" in text
    parts = [p for p in re.split(r"[^a-z0-9]+", kw) if len(p) > 2]
    if not parts:
        return kw in text
    return all(p in text for p in parts)


def main():
    pool = [norm_job(j) for j in json.loads(POOL.read_text())]
    kws = json.loads(KEYWORDS.read_text())
    lines = []
    for item in kws:
        kw = item["keyword"]
        group = item["group"]
        jobs = [j for j in pool if matches(kw, j)][:10]
        lines.append(json.dumps({"keyword": kw, "group": group, "jobs": jobs}, separators=(",", ":")))
    OUT.write_text("\n".join(lines) + "\n")
    print(f"Wrote {len(lines)} keyword rows, pool size {len(pool)}")


if __name__ == "__main__":
    main()
