#!/usr/bin/env python3
"""Append keyword search entries to run_data.jsonl from a batch JSON file."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "run_data.jsonl"


def main() -> None:
    batch = json.loads(Path(sys.argv[1]).read_text())
    if isinstance(batch, dict):
        batch = [batch]
    with OUT.open("a", encoding="utf-8") as f:
        for item in batch:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"appended {len(batch)} entries")


if __name__ == "__main__":
    main()
