#!/usr/bin/env python3
"""Read JSON array [{keyword, group, response}] from file or stdin; append to _search_queue.jsonl."""
import json, sys
from pathlib import Path

QUEUE = Path(__file__).resolve().parent / "_search_queue.jsonl"

def strip_job(j):
    j = dict(j)
    j.pop("description_snippet", None)
    return j

def flush_item(item):
    kw = item["keyword"]
    group = item["group"]
    resp = item.get("response") or {}
    if resp.get("status") == "error" or resp.get("error_code"):
        line = {"keyword": kw, "group": group, "status": "error", "error": resp.get("reason") or resp.get("error_code"), "jobs": []}
    else:
        jobs = [strip_job(j) for j in (resp.get("jobs") or [])]
        line = {"keyword": kw, "group": group, "status": "ok", "jobs": jobs}
    with QUEUE.open("a") as f:
        f.write(json.dumps(line, ensure_ascii=False) + "\n")

def main():
    src = sys.argv[1] if len(sys.argv) > 1 else None
    raw = Path(src).read_text() if src else sys.stdin.read()
    data = json.loads(raw)
    if not isinstance(data, list):
        data = [data]
    for item in data:
        flush_item(item)

if __name__ == "__main__":
    main()
