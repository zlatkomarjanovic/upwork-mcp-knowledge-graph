#!/usr/bin/env python3
"""Append one keyword search to _search_queue.jsonl. Usage: _queue_single.py KEYWORD GROUP RESPONSE.json"""
import json
import sys
from pathlib import Path

QUEUE = Path(__file__).resolve().parent / "_search_queue.jsonl"

def strip_job(j):
    j = dict(j)
    j.pop("description_snippet", None)
    return j

def main():
    kw, group, resp_path = sys.argv[1:4]
    resp = json.loads(Path(resp_path).read_text())
    if resp.get("status") == "error" or resp.get("error_code"):
        line = {"keyword": kw, "group": group, "status": "error", "error": resp.get("reason") or resp.get("error_code"), "jobs": []}
    else:
        jobs = [strip_job(j) for j in (resp.get("jobs") or [])]
        line = {"keyword": kw, "group": group, "status": "ok", "jobs": jobs}
    with QUEUE.open("a") as f:
        f.write(json.dumps(line, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    main()
