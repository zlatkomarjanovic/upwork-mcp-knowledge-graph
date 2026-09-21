#!/usr/bin/env python3
"""Append keyword->trace_id mappings for transcript pairing."""
import json
import sys
from pathlib import Path

INDEX = Path(__file__).parent / "search_index.jsonl"


def main() -> None:
    for line in sys.stdin.read().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        if len(parts) != 2:
            continue
        kw, trace = parts
        INDEX.parent.mkdir(parents=True, exist_ok=True)
        with INDEX.open("a") as f:
            f.write(json.dumps({"keyword": kw, "trace_id": trace}) + "\n")
    print(INDEX)


if __name__ == "__main__":
    main()
