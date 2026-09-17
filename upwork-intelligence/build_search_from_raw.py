#!/usr/bin/env python3
"""Build search_responses.json from raw_search_results.json."""
import json
from pathlib import Path

ROOT = Path(__file__).parent
GROUPS = json.loads((ROOT / "keywords.json").read_text())["keywords"]
RAW = ROOT / "raw_search_results.json"
SEARCH = ROOT / "search_responses.json"


def main() -> None:
    raw = json.loads(RAW.read_text()) if RAW.exists() else {"searches": []}
    by_kw = {s["keyword"]: s["response"] for s in raw.get("searches", [])}
    out = []
    for kw, group in GROUPS.items():
        resp = by_kw.get(kw) or {"status": "ok", "jobs": []}
        out.append({"keyword": kw, "group": group, "response": resp})
    SEARCH.write_text(json.dumps(out, indent=2))
    print(len(out), "keywords", len(by_kw), "with data")


if __name__ == "__main__":
    main()
