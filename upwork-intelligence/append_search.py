#!/usr/bin/env python3
"""Append one keyword search result line to run_data.jsonl."""
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
    return {k: j[k] for k in KEEP if k in j}


def main():
    keyword, group = sys.argv[1], sys.argv[2]
    payload = json.load(sys.stdin)
    row = {"keyword": keyword, "group": group}
    if payload.get("error"):
        row["error"] = payload["error"]
    elif payload.get("status") != "ok":
        row["error"] = payload.get("message") or "unknown_error"
    else:
        row["jobs"] = [compact_job(j) for j in payload.get("jobs") or []]
    with RUN_DATA.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
