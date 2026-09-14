#!/usr/bin/env python3
"""Merge batch JSON files (array of {keyword, jobs?, error?}) into raw-search-batch.jsonl."""
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
RAW = BASE / "raw-search-batch.jsonl"

def main():
    paths = sys.argv[1:]
    if not paths:
        paths = sorted(BASE.glob("batch_*.json"))
    lines = []
    for p in paths:
        data = json.loads(Path(p).read_text())
        if isinstance(data, dict):
            data = [data]
        for item in data:
            lines.append(json.dumps(item, ensure_ascii=False))
    RAW.write_text("\n".join(lines) + ("\n" if lines else ""))
    print(len(lines))

if __name__ == "__main__":
    main()
