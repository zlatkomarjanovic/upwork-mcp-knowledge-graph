#!/usr/bin/env python3
import json
import sys
from save_mcp_compact import save_item

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    d = json.loads(line)
    save_item(
        d["keyword"],
        d["group"],
        d.get("response") or {},
        d.get("error", False),
    )
print("saved", file=sys.stderr)
