#!/usr/bin/env python3
"""Merge keyword search chunk JSON into search_accum.json."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ACCUM = ROOT / "search_accum.json"


def main() -> None:
    chunk_path = Path(sys.argv[1])
    chunk = json.loads(chunk_path.read_text())
    accum: list = []
    if ACCUM.exists():
        accum = json.loads(ACCUM.read_text())
    known = {e["keyword"] for e in accum}
    for entry in chunk:
        if entry["keyword"] not in known:
            accum.append(entry)
            known.add(entry["keyword"])
    ACCUM.write_text(json.dumps(accum, ensure_ascii=False))


if __name__ == "__main__":
    main()
