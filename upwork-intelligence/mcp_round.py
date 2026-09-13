#!/usr/bin/env python3
"""Build ingest chunk from inline round data and append to search_log.jsonl."""
import json
import sys
from ingest_chunk import slim_response
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LOG = ROOT / "search_log.jsonl"


def ingest(entries: list[dict]) -> None:
    with LOG.open("a") as f:
        for entry in entries:
            row = {
                "keyword": entry["keyword"],
                "group": entry["group"],
                "response": slim_response(entry["response"]),
            }
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    ingest(json.loads(Path(sys.argv[1]).read_text()))
