#!/usr/bin/env python3
"""Print keywords missing from cache/ (for agent MCP batch runs)."""
import json
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).parent
kws = json.loads((ROOT / "keywords.json").read_text())["keywords"]
cache = ROOT / "cache"
missing = []
for kw in kws:
    if not (cache / f"{quote(kw, safe='')}.json").exists():
        missing.append(kw)
print(json.dumps({"missing": missing, "count": len(missing)}))
