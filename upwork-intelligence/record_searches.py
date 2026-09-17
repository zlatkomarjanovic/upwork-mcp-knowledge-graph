#!/usr/bin/env python3
"""Append keyword search results to _batch_results.jsonl (slim jobs, no descriptions)."""
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
OUT = BASE / "_batch_results.jsonl"
FIELDS = (
    "url",
    "title",
    "published_date",
    "created_date",
    "job_type",
    "budget",
    "duration",
    "proposals_tier",
    "experience_level",
    "skills",
)


def slim_jobs(jobs):
    out = []
    for j in jobs or []:
        row = {k: j[k] for k in FIELDS if k in j}
        row["client"] = j.get("client") or {}
        out.append(row)
    return out


def append_row(row):
    with OUT.open("a") as f:
        f.write(json.dumps(row, separators=(",", ":")) + "\n")


def main():
    data = json.load(sys.stdin)
    items = data if isinstance(data, list) else [data]
    for item in items:
        kw = item["keyword"]
        group = item["group"]
        mcp = item.get("mcp") or item.get("response") or {}
        if mcp.get("status") == "error" or item.get("error"):
            append_row(
                {
                    "keyword": kw,
                    "group": group,
                    "error": item.get("error")
                    or mcp.get("reason")
                    or mcp.get("error_code")
                    or "error",
                }
            )
        else:
            append_row(
                {
                    "keyword": kw,
                    "group": group,
                    "jobs": slim_jobs(mcp.get("jobs")),
                }
            )
    print(f"Appended {len(items)} rows to {OUT}")


if __name__ == "__main__":
    main()
