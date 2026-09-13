#!/usr/bin/env python3
"""Append labeled search results from a JSON file to batches.jsonl."""
import json
import sys
from pathlib import Path

BASE = Path(__file__).parent
path = BASE / "batches.jsonl"
items = json.loads(Path(sys.argv[1]).read_text())
with open(path, "a") as f:
    for item in items:
        resp = item.get("response") or {}
        jobs = resp.get("jobs", []) if resp.get("status") == "ok" else []
        err = resp.get("status") != "ok" or item.get("error")
        f.write(
            json.dumps(
                {
                    "keyword": item["keyword"],
                    "group": item["group"],
                    "jobs": jobs,
                    "error": bool(err and not jobs),
                }
            )
            + "\n"
        )
