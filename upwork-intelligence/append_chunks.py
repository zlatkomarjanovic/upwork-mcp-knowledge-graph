#!/usr/bin/env python3
"""Append keyword search chunks to _search_batches.jsonl."""
import json
import sys
from pathlib import Path

BATCH = Path(__file__).resolve().parent / "_search_batches.jsonl"


def main() -> None:
    data = json.loads(Path(sys.argv[1]).read_text())
    with BATCH.open("a", encoding="utf-8") as f:
        for item in data:
            line = {
                "keyword": item["keyword"],
                "jobs": item.get("jobs") or [],
                "error": item.get("error"),
            }
            f.write(json.dumps(line, ensure_ascii=False) + "\n")
    print(len(data))


if __name__ == "__main__":
    main()
