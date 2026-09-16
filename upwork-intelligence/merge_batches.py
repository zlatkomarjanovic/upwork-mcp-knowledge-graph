#!/usr/bin/env python3
"""Merge batch search JSON files into run payload for aggregate.py."""
import json
import glob
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
BATCH_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/upwork_run2")

keywords = []
errors = []
for fp in sorted(BATCH_DIR.glob("batch*.json")):
    data = json.loads(fp.read_text())
    if isinstance(data, list):
        keywords.extend(data)
    else:
        keywords.extend(data.get("keywords", []))
        errors.extend(data.get("errors", []))

# dedupe keywords by name (last wins)
by_kw = {}
for k in keywords:
    by_kw[k["keyword"]] = k
keywords = list(by_kw.values())

for k in keywords:
    if not k.get("ok", True) and k["keyword"] not in errors:
        errors.append(k["keyword"])

payload = {
    "lastRunAt": datetime.now(timezone.utc).isoformat(),
    "windowHours": 1,
    "keywords": keywords,
    "errors": sorted(set(errors)),
}
out = BASE / "run_payload.json"
out.write_text(json.dumps(payload, ensure_ascii=False))
print(json.dumps({"keywords": len(keywords), "errors": len(payload["errors"])}))
