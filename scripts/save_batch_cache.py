#!/usr/bin/env python3
"""Import [{keyword, response}, ...] JSON array into cache/."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upwork-intelligence" / "cache"


def slug(kw: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", kw.lower()).strip("-")


def main() -> int:
    items = json.loads(Path(sys.argv[1]).read_text())
    ROOT.mkdir(parents=True, exist_ok=True)
    for row in items:
        kw = row["keyword"]
        (ROOT / f"{slug(kw)}.json").write_text(json.dumps(row["response"]))
    print(len(items))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
