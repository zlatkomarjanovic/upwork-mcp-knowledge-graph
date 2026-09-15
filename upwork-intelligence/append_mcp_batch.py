#!/usr/bin/env python3
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
BULK = BASE / "mcp_queue" / "_bulk.json"
BULK.parent.mkdir(exist_ok=True)


def main():
    new_items = json.loads(Path(sys.argv[1]).read_text())
    if isinstance(new_items, dict):
        new_items = new_items.get("items", [])
    existing = []
    if BULK.exists() and BULK.read_text().strip():
        existing = json.loads(BULK.read_text())
    existing.extend(new_items)
    BULK.write_text(json.dumps(existing, ensure_ascii=False))
    print(len(existing))


if __name__ == "__main__":
    main()
