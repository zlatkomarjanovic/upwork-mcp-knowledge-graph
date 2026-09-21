#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).parent
CACHE = ROOT / "cache"
SEARCH = ROOT / "search_responses.json"
GROUPS = json.loads((ROOT / "keywords.json").read_text())["keywords"]


def main():
    base = []
    if SEARCH.exists():
        base = json.loads(SEARCH.read_text())
    by_kw = {e["keyword"]: e for e in base}
    for path in CACHE.glob("*.json"):
        data = json.loads(path.read_text())
        kw = data["keyword"]
        by_kw[kw] = {"keyword": kw, "group": GROUPS.get(kw, "OTHER"), "response": data["response"]}
    paired = []
    for k in GROUPS:
        if k in by_kw:
            paired.append(by_kw[k])
        elif k in {e["keyword"] for e in base}:
            paired.append(next(e for e in base if e["keyword"] == k))
    SEARCH.write_text(json.dumps(paired, indent=2))
    print(len(paired))


if __name__ == "__main__":
    main()
