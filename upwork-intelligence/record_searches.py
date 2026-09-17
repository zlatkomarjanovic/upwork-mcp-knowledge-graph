#!/usr/bin/env python3
"""Append MCP search rows to raw-searches.jsonl. stdin: JSON array or single object with keyword + response/error."""
import json, sys
from pathlib import Path

OUT = Path(__file__).parent / "raw-searches.jsonl"

def append_row(row):
    if "keyword" not in row:
        raise SystemExit("missing keyword")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")

def main():
    raw = sys.stdin.read().strip()
    if not raw:
        return
    data = json.loads(raw)
    if isinstance(data, list):
        for row in data:
            append_row(row)
    else:
        append_row(data)

if __name__ == "__main__":
    main()
