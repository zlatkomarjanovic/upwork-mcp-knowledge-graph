#!/usr/bin/env python3
"""Append keyword search entries to a single accumulating batch file."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ACCUM = ROOT / "search_accum.json"


def main() -> None:
    entries = json.loads(ACCUM.read_text()) if ACCUM.exists() else []
    for path in sys.argv[1:]:
        entries.append(json.loads(Path(path).read_text()))
    ACCUM.write_text(json.dumps(entries, ensure_ascii=False))


if __name__ == "__main__":
    main()
