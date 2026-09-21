#!/usr/bin/env python3
"""Overlay cache/*.json responses onto search_responses.json by keyword."""
import json
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).parent
CACHE = ROOT / "cache"
SEARCH = ROOT / "search_responses.json"
GROUPS = json.loads((ROOT / "keywords.json").read_text())["keywords"]


def main() -> None:
    paired = json.loads(SEARCH.read_text())
    index = {e["keyword"]: i for i, e in enumerate(paired)}
    updated = 0
    for path in CACHE.glob("*.json"):
        data = json.loads(path.read_text())
        kw = data.get("keyword") or unquote(path.stem)
        resp = data.get("response") or data
        entry = {"keyword": kw, "group": GROUPS.get(kw, "OTHER"), "response": resp}
        if kw in index:
            paired[index[kw]] = entry
        else:
            paired.append(entry)
        updated += 1
    SEARCH.write_text(json.dumps(paired, indent=2))
    print("updated", updated)


if __name__ == "__main__":
    main()
