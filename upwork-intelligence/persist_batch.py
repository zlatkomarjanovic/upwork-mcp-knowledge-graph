#!/usr/bin/env python3
"""Append keyword search entries to search_responses.json. Usage: persist_batch.py entries.json"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "search_responses.json"


def main() -> None:
    new_entries = json.loads(Path(sys.argv[1]).read_text())
    existing = json.loads(OUT.read_text()) if OUT.exists() else []
    seen = {e.get("keyword") for e in existing}
    for e in new_entries:
        if e.get("keyword") not in seen:
            existing.append(e)
            seen.add(e.get("keyword"))
    OUT.write_text(json.dumps(existing, ensure_ascii=False))
    print(len(existing))


if __name__ == "__main__":
    main()
