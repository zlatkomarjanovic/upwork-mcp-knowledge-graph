#!/usr/bin/env python3
"""Print keywords missing fresh mcp_raw JSON files."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "mcp_raw"
keywords = json.loads((ROOT / "keywords.json").read_text())


def slug(kw: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", kw.lower()).strip("_")


missing = []
for k in keywords:
    kw = k["keyword"]
    p = RAW / f"{slug(kw)}.json"
    if not p.exists():
        missing.append(kw)

print(json.dumps(missing))
