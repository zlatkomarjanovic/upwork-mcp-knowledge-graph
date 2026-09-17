#!/usr/bin/env python3
"""Append batch of search results to run_data.jsonl. stdin: JSON array of {keyword, group, jobs|error}."""
import json
import sys
from pathlib import Path

RUN_DATA = Path(__file__).resolve().parent / "run_data.jsonl"
KEEP = (
    "url",
    "title",
    "published_date",
    "job_type",
    "budget",
    "duration",
    "experience_level",
    "proposals_tier",
    "skills",
    "client",
)


def compact_job(j):
    out = {k: j[k] for k in KEEP if k in j}
    if out.get("url"):
        out["url"] = out["url"].split("?")[0]
    return out


def main():
    batch = json.load(sys.stdin)
    with RUN_DATA.open("a", encoding="utf-8") as f:
        for item in batch:
            row = {"keyword": item["keyword"], "group": item["group"]}
            if item.get("error"):
                row["error"] = item["error"]
            else:
                row["jobs"] = [compact_job(j) for j in item.get("jobs") or []]
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
