#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
OUT = BASE / "mcp_raw"
OUT.mkdir(exist_ok=True)


def slug(kw: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", kw.lower()).strip("_") or "kw"


def main():
    path = Path(sys.argv[1])
    items = json.loads(path.read_text())
    if isinstance(items, dict) and "searches" in items:
        items = items["searches"]
    for item in items:
        kw = item["keyword"]
        (OUT / f"{slug(kw)}.json").write_text(json.dumps(item, ensure_ascii=False))


if __name__ == "__main__":
    main()
