#!/usr/bin/env python3
"""Append one batch file (JSON list of {keyword, group, response}) to _search_queue.jsonl."""
import json, sys
from pathlib import Path

QUEUE = Path(__file__).resolve().parent / "_search_queue.jsonl"

def flush_item(item):
    kw = item["keyword"]
    group = item["group"]
    resp = item.get("response") or {}
    if resp.get("status") == "error" or resp.get("error_code"):
        line = {"keyword": kw, "group": group, "status": "error", "error": resp.get("reason") or resp.get("error_code"), "jobs": []}
    else:
        line = {"keyword": kw, "group": group, "status": "ok", "jobs": resp.get("jobs") or []}
    with QUEUE.open("a") as f:
        f.write(json.dumps(line, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    for path in sys.argv[1:]:
        data = json.loads(Path(path).read_text())
        if isinstance(data, list):
            for item in data:
                flush_item(item)
        else:
            flush_item(data)
