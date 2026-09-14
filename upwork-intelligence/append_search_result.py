#!/usr/bin/env python3
"""Append one or more JSON lines to search_results.jsonl (keyword search payloads)."""
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
OUT = BASE / "search_results.jsonl"


def main():
    data = sys.stdin.read()
    if not data.strip():
        return
    with OUT.open("a") as f:
        if data.lstrip().startswith("["):
            for item in json.loads(data):
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        else:
            for line in data.splitlines():
                if line.strip():
                    f.write(line.rstrip() + "\n")
    print("appended")


if __name__ == "__main__":
    main()
