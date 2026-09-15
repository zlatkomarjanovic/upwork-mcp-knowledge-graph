#!/usr/bin/env python3
"""Build search_responses.json from raw_search_results.json for all configured keywords."""
import json
from pathlib import Path

ROOT = Path(__file__).parent
GROUPS = json.loads((ROOT / "keywords.json").read_text())["keywords"]
RAW = ROOT / "raw_search_results.json"
SEARCH = ROOT / "search_responses.json"

raw = {"searches": [], "errors": []}
if RAW.exists():
    raw = json.loads(RAW.read_text())
by_kw = {s["keyword"]: s["response"] for s in raw.get("searches", [])}
paired = []
for kw, group in GROUPS.items():
    resp = by_kw.get(kw)
    if resp is None:
        resp = {"status": "error", "jobs": []}
    paired.append({"keyword": kw, "group": group, "response": resp})
SEARCH.write_text(json.dumps(paired, indent=2))
print(
    json.dumps(
        {
            "keywords": len(paired),
            "filled": sum(1 for kw in GROUPS if kw in by_kw),
            "errors": raw.get("errors", []),
        }
    )
)
