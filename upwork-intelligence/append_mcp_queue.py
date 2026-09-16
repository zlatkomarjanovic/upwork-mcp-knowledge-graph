#!/usr/bin/env python3
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
QUEUE = BASE / "mcp-queue.jsonl"


def strip_job(j):
    return {
        k: j.get(k)
        for k in (
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
            "client",
            "description_snippet",
        )
    }


def main():
    payload = json.load(sys.stdin)
    for entry in payload.get("results", []):
        line = {
            "keyword": entry["keyword"],
            "group": entry["group"],
            "jobs": [strip_job(j) for j in entry.get("jobs", [])],
            "error": entry.get("error"),
        }
        with QUEUE.open("a") as f:
            f.write(json.dumps(line, ensure_ascii=False) + "\n")
    print(json.dumps({"appended": len(payload.get("results", []))}))


if __name__ == "__main__":
    main()
