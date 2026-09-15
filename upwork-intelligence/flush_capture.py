#!/usr/bin/env python3
"""Load capture.jsonl into mcp_raw (one JSON object per line)."""
import json
from pathlib import Path

from record_batch import save_item

CAP = Path(__file__).resolve().parent / "capture.jsonl"


def main():
    if not CAP.exists():
        print("no capture.jsonl")
        return
    n = 0
    seen = set()
    with CAP.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            kw = row["keyword"]
            if kw in seen:
                continue
            seen.add(kw)
            save_item(kw, row["response"])
            n += 1
    print("flushed", n)


if __name__ == "__main__":
    main()
