#!/usr/bin/env python3
"""Append search results to _search_queue.jsonl. stdin: JSON array of {keyword, group, response}."""
import json, sys
from pathlib import Path

QUEUE = Path(__file__).resolve().parent / "_search_queue.jsonl"

def main():
    data = json.load(sys.stdin)
    with QUEUE.open("a") as f:
        for item in data:
            kw = item["keyword"]
            group = item["group"]
            resp = item.get("response") or {}
            if resp.get("status") == "error" or resp.get("error_code"):
                f.write(json.dumps({"keyword": kw, "group": group, "status": "error", "error": resp.get("reason") or resp.get("error_code"), "jobs": []}) + "\n")
            else:
                f.write(json.dumps({"keyword": kw, "group": group, "status": "ok", "jobs": resp.get("jobs") or []}) + "\n")

if __name__ == "__main__":
    main()
