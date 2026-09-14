#!/usr/bin/env python3
"""Append search batch lines from stdin JSON array to raw-search-batch.jsonl."""
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
RAW = BASE / "raw-search-batch.jsonl"


def main():
    data = json.load(sys.stdin)
    if isinstance(data, dict):
        data = [data]
    with RAW.open("a") as f:
        for item in data:
            kw = item.get("keyword")
            if item.get("error") or item.get("status") == "error":
                line = {
                    "keyword": kw,
                    "jobs": [],
                    "error": item.get("error") or item.get("reason") or item.get("error_code"),
                }
            else:
                resp = item.get("response") or item
                jobs = resp.get("jobs", []) if isinstance(resp, dict) else []
                line = {"keyword": kw, "jobs": jobs}
            f.write(json.dumps(line, ensure_ascii=False) + "\n")
    print(len(data))


if __name__ == "__main__":
    main()
