#!/usr/bin/env python3
"""Append batch of {keyword, group, response} objects to search_results.jsonl."""
import json
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent / "search_results.jsonl"


def main():
    data = json.load(sys.stdin)
    items = data if isinstance(data, list) else data.get("items", [])
    with OUT.open("a") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(len(items))


if __name__ == "__main__":
    main()
