#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).parent
CACHE = ROOT / "cache"
SEARCH = ROOT / "search_responses.json"
GROUPS = json.loads((ROOT / "keywords.json").read_text())["keywords"]


def main():
    paired = []
    for path in sorted(CACHE.glob("*.json")):
        data = json.loads(path.read_text())
        kw = data["keyword"]
        paired.append({"keyword": kw, "group": GROUPS.get(kw, "OTHER"), "response": data["response"]})
    paired.sort(key=lambda x: list(GROUPS.keys()).index(x["keyword"]) if x["keyword"] in GROUPS else 999)
    SEARCH.write_text(json.dumps(paired, indent=2))
    print(len(paired))


if __name__ == "__main__":
    main()
