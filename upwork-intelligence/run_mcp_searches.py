#!/usr/bin/env python3
"""List keywords missing from mcp_raw (for agent search queue)."""
import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent
MCP_RAW = BASE / "mcp_raw"
KEYWORDS = BASE / "keywords.json"


def slug(kw: str) -> str:
    return re.sub(r"[^\w\- ]", "_", kw)[:80].strip()


def main():
    with open(KEYWORDS) as f:
        groups = json.load(f)
    all_kw = [kw for kws in groups.values() for kw in kws]
    missing = []
    for kw in all_kw:
        if not (MCP_RAW / f"{slug(kw)}.json").exists():
            missing.append(kw)
    print(json.dumps({"total": len(all_kw), "missing": len(missing), "keywords": missing}))


if __name__ == "__main__":
    main()
