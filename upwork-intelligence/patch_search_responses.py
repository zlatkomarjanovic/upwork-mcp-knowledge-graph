#!/usr/bin/env python3
"""Patch search_responses.json with fresh MCP results. stdin: [{keyword, response}, ...]"""
import json
import sys
from pathlib import Path

from write_cache_batch import slim

ROOT = Path(__file__).parent
SEARCH = ROOT / "search_responses.json"
ORDER = list(json.loads((ROOT / "keywords.json").read_text())["keywords"].keys())


def main() -> None:
    batch = json.load(sys.stdin)
    paired = json.loads(SEARCH.read_text())
    by_kw = {p["keyword"]: p for p in paired}
    for item in batch:
        kw = item["keyword"]
        if kw not in by_kw:
            by_kw[kw] = {"keyword": kw, "group": item.get("group", ""), "response": {}}
        by_kw[kw]["response"] = slim(item["response"])
    paired = [by_kw[k] for k in ORDER if k in by_kw]
    SEARCH.write_text(json.dumps(paired, indent=2))
    print(len(batch), flush=True)


if __name__ == "__main__":
    main()
