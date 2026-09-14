#!/usr/bin/env python3
"""Append one search result line to raw-search-batch.jsonl. Usage: append_search_result.py KEYWORD [jobs.json]"""
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
RAW = BASE / "raw-search-batch.jsonl"

def main():
    kw = sys.argv[1]
    if len(sys.argv) > 2:
        jobs = json.loads(Path(sys.argv[2]).read_text())
    else:
        jobs = json.load(sys.stdin)
    line = json.dumps({"keyword": kw, "jobs": jobs}, ensure_ascii=False)
    with RAW.open("a") as f:
        f.write(line + "\n")

if __name__ == "__main__":
    main()
