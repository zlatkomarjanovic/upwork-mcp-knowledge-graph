#!/usr/bin/env python3
"""Append keyword search entries to run-results.jsonl or raw_search_results.json."""
import json
import sys
from pathlib import Path

BASE = Path(__file__).parent
RAW = BASE / "raw_search_results.json"
JSONL = BASE / "run-results.jsonl"


def append_jsonl(entries: list[dict]):
    with JSONL.open("a") as f:
        for e in entries:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")


def merge_raw(entries: list[dict]):
    data = {"searches": [], "errors": []}
    if RAW.exists():
        data = json.loads(RAW.read_text())
    for e in entries:
        data["searches"].append(e)
    RAW.write_text(json.dumps(data, indent=2))


def main():
    payload = json.loads(sys.stdin.read())
    entries = payload if isinstance(payload, list) else payload.get("entries", [])
    merge_raw(entries)
    append_jsonl([{"keyword": e["keyword"], "response": e.get("response")} for e in entries])
    print(json.dumps({"appended": len(entries)}, indent=2))


if __name__ == "__main__":
    main()
