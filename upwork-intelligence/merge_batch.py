#!/usr/bin/env python3
"""Append MCP search batch rows to _batch_results.jsonl. Usage: merge_batch.py batch.json"""
import json, sys
from pathlib import Path

OUT = Path(__file__).parent / "_batch_results.jsonl"

def main():
    p = Path(sys.argv[1])
    data = json.loads(p.read_text())
    if isinstance(data, dict):
        data = [data]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("a", encoding="utf-8") as f:
        for row in data:
            if "keyword" not in row:
                continue
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    main()
