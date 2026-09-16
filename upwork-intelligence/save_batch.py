#!/usr/bin/env python3
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent
SEARCH = ROOT / "search_responses.json"
GROUPS = json.loads((ROOT / "keywords.json").read_text())["keywords"]


def main():
    batch = json.loads(sys.stdin.read())
    paired = json.loads(SEARCH.read_text()) if SEARCH.exists() else []
    index = {e["keyword"]: i for i, e in enumerate(paired)}
    for item in batch:
        kw = item["keyword"]
        entry = {"keyword": kw, "group": GROUPS.get(kw, "OTHER"), "response": item["response"]}
        if kw in index:
            paired[index[kw]] = entry
        else:
            paired.append(entry)
            index[kw] = len(paired) - 1
    SEARCH.write_text(json.dumps(paired, indent=2))
    print(len(paired))


if __name__ == "__main__":
    main()
