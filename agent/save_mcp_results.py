#!/usr/bin/env python3
"""Save MCP batch file: JSON {searches:[{keyword,group,response:{jobs}}]} or array of same."""
import json
import sys
from pathlib import Path

import record_search

PARTIAL = Path(__file__).resolve().parent / "partial"


def save_one(keyword, group, jobs):
    entry = {"keyword": keyword, "group": group, "jobs": jobs or []}
    PARTIAL.mkdir(parents=True, exist_ok=True)
    out = PARTIAL / f"{record_search.slug(keyword)}.json"
    out.write_text(json.dumps(entry, indent=2))
    return len(jobs or [])


def main():
    path = Path(sys.argv[1])
    data = json.loads(path.read_text())
    items = data if isinstance(data, list) else data.get("searches", [data])
    total_jobs = 0
    for item in items:
        kw = item["keyword"]
        group = item["group"]
        resp = item.get("response") or item
        jobs = resp.get("jobs", []) if isinstance(resp, dict) else item.get("jobs", [])
        total_jobs += save_one(kw, group, jobs)
    print("partials", len(items), "jobs", total_jobs)


if __name__ == "__main__":
    main()
