#!/usr/bin/env python3
import json
import sys
from pathlib import Path

base_path = Path(__file__).parent / "raw_batch.json"
data = json.loads(base_path.read_text())
chunk = json.loads(sys.stdin.read())
for item in chunk:
    data["searches"].append(item)
    kw = item["keyword"]
    resp = item.get("response") or {}
    if resp.get("status") == "ok" or "jobs" in resp:
        if kw not in data.get("_completed", []):
            data.setdefault("_completed", []).append(kw)
    else:
        if kw not in data["errors"]:
            data["errors"].append(kw)
data["keywordsCompleted"] = len(data["searches"])
if "_completed" in data:
    del data["_completed"]
base_path.write_text(json.dumps(data))
