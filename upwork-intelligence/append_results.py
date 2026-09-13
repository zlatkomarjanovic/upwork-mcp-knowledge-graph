#!/usr/bin/env python3
"""Append batch keyword MCP results to search_log.jsonl (slim jobs)."""
import json
import sys
from pathlib import Path

from ingest_chunk import slim_response

LOG = Path(__file__).resolve().parent / "search_log.jsonl"


def main() -> None:
    chunk = json.loads(Path(sys.argv[1]).read_text())
    with LOG.open("a") as f:
        for entry in chunk:
            row = {
                "keyword": entry["keyword"],
                "group": entry["group"],
                "response": slim_response(entry.get("response") or {}),
            }
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"Appended {len(chunk)} entries")


if __name__ == "__main__":
    main()
