#!/usr/bin/env python3
"""Merge search_responses.json into _run_raw.json searches dict."""
import json
from pathlib import Path

BASE = Path(__file__).parent
raw_path = BASE / "_run_raw.json"
resp_path = BASE / "search_responses.json"
if not resp_path.exists():
    raise SystemExit("no search_responses.json")
data = json.loads(raw_path.read_text()) if raw_path.exists() else {"searches": {}, "errors": []}
searches = data.setdefault("searches", {})
for entry in json.loads(resp_path.read_text()):
    kw = entry["keyword"]
    resp = entry.get("response") or {}
    if resp.get("status") == "ok":
        searches[kw] = {"status": "ok", "jobs": resp.get("jobs") or []}
    else:
        data.setdefault("errors", [])
        if kw not in data["errors"]:
            data["errors"].append(kw)
raw_path.write_text(json.dumps(data))
print("merged", len(json.loads(resp_path.read_text())), "keywords; total keys", len(searches))
