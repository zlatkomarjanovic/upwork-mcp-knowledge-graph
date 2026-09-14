#!/usr/bin/env python3
"""Append batch JSON file(s) to raw-search-batch.jsonl. Each file: [{keyword, response|jobs, error?}]"""
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
RAW = BASE / "raw-search-batch.jsonl"


def append_item(item):
    kw = item.get("keyword")
    if item.get("error"):
        line = {"keyword": kw, "jobs": [], "error": item["error"]}
    else:
        resp = item.get("response") or item
        jobs = resp.get("jobs", []) if isinstance(resp, dict) else item.get("jobs", [])
        line = {"keyword": kw, "jobs": jobs}
    with RAW.open("a") as f:
        f.write(json.dumps(line, ensure_ascii=False) + "\n")


def main():
    for path in sys.argv[1:]:
        data = json.loads(Path(path).read_text())
        if isinstance(data, dict):
            data = [data]
        for item in data:
            append_item(item)
    print(RAW.read_text().count("\n"))


if __name__ == "__main__":
    main()
