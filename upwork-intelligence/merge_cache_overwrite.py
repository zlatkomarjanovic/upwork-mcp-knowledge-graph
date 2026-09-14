#!/usr/bin/env python3
"""Merge cache/*.json over existing search_responses.json entries."""
import json
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).parent
CACHE = ROOT / "cache"
SEARCH = ROOT / "search_responses.json"
GROUPS = json.loads((ROOT / "keywords.json").read_text())["keywords"]


def main() -> None:
    paired = json.loads(SEARCH.read_text()) if SEARCH.exists() else []
    index = {e["keyword"]: i for i, e in enumerate(paired)}
    updated = 0
    for path in CACHE.glob("*.json"):
        data = json.loads(path.read_text())
        kw = data["keyword"]
        entry = {
            "keyword": kw,
            "group": GROUPS.get(kw, "OTHER"),
            "response": data["response"],
        }
        if kw in index:
            paired[index[kw]] = entry
        else:
            paired.append(entry)
            index[kw] = len(paired) - 1
        updated += 1
    paired.sort(key=lambda x: list(GROUPS.keys()).index(x["keyword"]))
    SEARCH.write_text(json.dumps(paired, indent=2))
    print(json.dumps({"updated_from_cache": updated, "total": len(paired)}))


if __name__ == "__main__":
    main()
