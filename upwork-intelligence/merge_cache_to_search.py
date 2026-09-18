#!/usr/bin/env python3
"""Apply cache/*.json over search_responses.json entries."""
import json
from pathlib import Path
from urllib.parse import quote, unquote

ROOT = Path(__file__).parent
CACHE = ROOT / "cache"
SEARCH = ROOT / "search_responses.json"
GROUPS = json.loads((ROOT / "keywords.json").read_text())["keywords"]


def main() -> None:
    paired = json.loads(SEARCH.read_text()) if SEARCH.exists() else []
    index = {e["keyword"]: i for i, e in enumerate(paired)}
    updated = 0
    for path in CACHE.glob("*.json"):
        item = json.loads(path.read_text())
        kw = item["keyword"]
        entry = {
            "keyword": kw,
            "group": GROUPS.get(kw, "OTHER"),
            "response": item["response"],
        }
        if kw in index:
            paired[index[kw]] = entry
        else:
            paired.append(entry)
            index[kw] = len(paired) - 1
        updated += 1
    SEARCH.write_text(json.dumps(paired, ensure_ascii=False))
    print(json.dumps({"updated": updated, "total": len(paired)}))


if __name__ == "__main__":
    main()
