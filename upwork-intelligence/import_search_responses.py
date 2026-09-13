#!/usr/bin/env python3
"""Convert search_responses.json array to run-results.jsonl."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent
src = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "search_responses.json"
out = ROOT / "run-results.jsonl"
data = json.loads(src.read_text())
if isinstance(data, dict):
    data = data.get("searches") or data.get("results") or list(data.values())
with out.open("w") as f:
    for item in data:
        kw = item.get("keyword")
        group = item.get("group")
        jobs = (item.get("response") or {}).get("jobs") or item.get("jobs") or []
        f.write(json.dumps({"keyword": kw, "group": group, "jobs": jobs}, ensure_ascii=False) + "\n")
print("wrote", len(data), "lines to", out)
