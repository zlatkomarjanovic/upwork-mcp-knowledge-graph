#!/usr/bin/env python3
"""Update one keyword entry in search_responses.json."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent
SEARCH = ROOT / "search_responses.json"
GROUPS = json.loads((ROOT / "keywords.json").read_text())["keywords"]


def main():
    kw = sys.argv[1]
    resp = json.loads(Path(sys.argv[2]).read_text())
    paired = json.loads(SEARCH.read_text())
    group = GROUPS.get(kw, "OTHER")
    updated = False
    for i, entry in enumerate(paired):
        if entry["keyword"] == kw:
            paired[i] = {"keyword": kw, "group": group, "response": resp}
            updated = True
            break
    if not updated:
        paired.append({"keyword": kw, "group": group, "response": resp})
    SEARCH.write_text(json.dumps(paired, indent=2))


if __name__ == "__main__":
    main()
