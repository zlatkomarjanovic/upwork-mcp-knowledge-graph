#!/usr/bin/env python3
"""Import MCP search results from JSONL into upwork-intelligence/cache/."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upwork-intelligence" / "cache"


def slug(kw: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", kw.lower()).strip("-")


def main() -> int:
    path = Path(sys.argv[1])
    ROOT.mkdir(parents=True, exist_ok=True)
    n = 0
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        kw = row["keyword"]
        (ROOT / f"{slug(kw)}.json").write_text(json.dumps(row["response"]))
        n += 1
    print(n)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
