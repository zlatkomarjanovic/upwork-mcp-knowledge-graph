#!/usr/bin/env python3
"""Convert search-raw.json to search_responses.json for process_run.py."""
import json
from pathlib import Path

ROOT = Path(__file__).parent
RAW = ROOT / "search-raw.json"
OUT = ROOT / "search_responses.json"
GROUPS = json.loads((ROOT / "keywords.json").read_text())["keywords"]


def main():
    if not RAW.exists():
        raise SystemExit("Missing search-raw.json")
    data = json.loads(RAW.read_text())
    by_kw = {r["keyword"]: r["result"] for r in data.get("results", [])}
    paired = []
    for kw, group in GROUPS.items():
        resp = by_kw.get(kw) or {"status": "error", "error_code": "MISSING_SEARCH", "jobs": []}
        paired.append({"keyword": kw, "group": group, "response": resp})
    OUT.write_text(json.dumps(paired, indent=2))
    ok = sum(1 for p in paired if p["response"].get("status") == "ok")
    print(json.dumps({"keywords": len(paired), "ok": ok}))


if __name__ == "__main__":
    main()
