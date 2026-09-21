#!/usr/bin/env python3
"""Append search rows to search_raw.ndjson. Stdin: JSON array of {keyword, group, jobs?, error?}."""
import json, sys
from pathlib import Path

RAW = Path(__file__).parent / "search_raw.ndjson"

def slim_job(j):
    if not isinstance(j, dict):
        return j
    drop = {"description_snippet", "client_rating_basis"}
    return {k: v for k, v in j.items() if k not in drop}

def main():
    data = json.load(sys.stdin)
    if isinstance(data, dict):
        data = [data]
    with RAW.open("a") as f:
        for rec in data:
            jobs = rec.get("jobs")
            if jobs:
                rec = {**rec, "jobs": [slim_job(j) for j in jobs]}
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    main()
