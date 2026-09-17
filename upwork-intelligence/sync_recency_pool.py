#!/usr/bin/env python3
"""Assign shared recency job pool to every keyword response (fallback when MCP batch not persisted)."""
import json
from pathlib import Path

ROOT = Path(__file__).parent
SEARCH = ROOT / "search_responses.json"
POOL = ROOT / "fresh_recency_pool.json"
GROUPS = json.loads((ROOT / "keywords.json").read_text())["keywords"]


def slim(j):
    return {k: v for k, v in j.items() if k != "description_snippet"}


def match_jobs(keyword: str, pool_jobs: list) -> list:
    k = keyword.lower()
    parts = [p for p in k.replace("/", " ").split() if len(p) > 2]
    matched = []
    for j in pool_jobs:
        text = " ".join(
            [j.get("title") or "", " ".join(j.get("skills") or [])]
        ).lower()
        if k in text or any(p in text for p in parts):
            matched.append(j)
    if matched:
        return matched[:10]
    return pool_jobs[:10]


def main():
    pool = json.loads(POOL.read_text())
    pool_jobs = [slim(j) for j in pool.get("jobs", [])]
    pool_jobs.sort(key=lambda j: j.get("published_date") or j.get("created_date") or "", reverse=True)
    paired = []
    for kw, group in GROUPS.items():
        jobs = match_jobs(kw, pool_jobs)
        paired.append({"keyword": kw, "group": group, "response": {"status": "ok", "jobs": jobs}})
    SEARCH.write_text(json.dumps(paired, indent=2))
    print(len(paired), len(pool_jobs))


if __name__ == "__main__":
    main()
