#!/usr/bin/env python3
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
FIELDS = (
    "url",
    "title",
    "published_date",
    "created_date",
    "job_type",
    "budget",
    "duration",
    "proposal_count",
    "experience_level",
    "skills",
    "client",
)


def slim_job(j):
    return {k: j.get(k) for k in FIELDS}


def slim(resp):
    if resp.get("status") == "error":
        return {
            "status": "error",
            "error_code": resp.get("error_code"),
            "reason": resp.get("reason"),
        }
    return {"status": "ok", "jobs": [slim_job(j) for j in resp.get("jobs") or []]}


def main():
    raw_path = BASE / "_raw_run.json"
    raw = json.loads(raw_path.read_text())
    entries = json.load(sys.stdin)
    if isinstance(entries, dict) and "keyword" in entries:
        entries = [entries]
    for entry in entries:
        raw["searches"].append(
            {"keyword": entry["keyword"], "response": slim(entry["response"])}
        )
    raw["meta"]["keywordsCompleted"] = len(raw["searches"])
    raw_path.write_text(json.dumps(raw))
    print(len(raw["searches"]))


if __name__ == "__main__":
    main()
