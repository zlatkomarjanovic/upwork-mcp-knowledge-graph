#!/usr/bin/env python3
"""Merge batch search results into mcp_raw/*.json"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "mcp_raw"
RAW.mkdir(exist_ok=True)


def slug(kw: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", kw.lower()).strip("_")


def main() -> None:
    batch = json.loads(Path(sys.argv[1]).read_text())
    for item in batch:
        kw = item.get("keyword", "unknown")
        path = RAW / f"{slug(kw)}.json"
        path.write_text(json.dumps(item, ensure_ascii=False))


if __name__ == "__main__":
    main()
