#!/usr/bin/env python3
"""Merge batch file of {keyword, group, response} into search-results-raw.json."""
import json
import sys
from pathlib import Path

path = Path(__file__).parent / "search-results-raw.json"
data = json.loads(path.read_text())
batch = json.loads(Path(sys.argv[1]).read_text())
for item in batch:
    resp = item.get("response") or {}
    if isinstance(resp, str):
        try:
            resp = json.loads(resp)
        except json.JSONDecodeError:
            resp = {"status": "error", "message": resp}
    err = item.get("error") or resp.get("status") not in ("ok", None)
    if resp.get("status") == "ok":
        err = False
    entry = {
        "keyword": item["keyword"],
        "group": item["group"],
        "jobs": resp.get("jobs", []),
    }
    if err:
        entry["error"] = True
        data.setdefault("errors", []).append(item["keyword"])
    data["searches"].append(entry)
path.write_text(json.dumps(data))
print(len(data["searches"]), "searches stored")
