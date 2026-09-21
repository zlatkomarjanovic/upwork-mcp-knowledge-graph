#!/usr/bin/env python3
import json
from pathlib import Path

from save_mcp_compact import save_item

BASE = Path(__file__).resolve().parent
INCOMING = BASE / "incoming"
groups = json.loads((BASE / "keyword_to_group.json").read_text())
INCOMING.mkdir(exist_ok=True)
n = 0
for p in INCOMING.glob("*.json"):
    data = json.loads(p.read_text())
    kw = data["keyword"]
    save_item(kw, groups[kw], data.get("response") or {}, data.get("error", False))
    p.unlink()
    n += 1
print(n)
