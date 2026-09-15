#!/usr/bin/env python3
"""Append slim search results to _search_queue.jsonl. stdin: [{keyword, response}, ...]"""
import json
import sys
from pathlib import Path

from _add_searches import slim

BASE = Path(__file__).resolve().parent
QUEUE = BASE / "_search_queue.jsonl"


def main():
    data = json.load(sys.stdin)
    if isinstance(data, dict):
        data = [data]
    with QUEUE.open("a") as f:
        for item in data:
            f.write(
                json.dumps(
                    {"keyword": item["keyword"], "response": slim(item["response"])},
                    separators=(",", ":"),
                )
                + "\n"
            )
    print(len(data))


if __name__ == "__main__":
    main()
