#!/usr/bin/env python3
"""Merge captured live MCP search payloads into search_responses.json."""
import json
from pathlib import Path

ROOT = Path(__file__).parent
CAPTURE = ROOT / "run3_capture.json"
SEARCH = ROOT / "search_responses.json"
GROUPS = json.loads((ROOT / "keywords.json").read_text())["keywords"]

def main():
    capture = json.loads(CAPTURE.read_text())
    paired = json.loads(SEARCH.read_text())
    index = {e["keyword"]: i for i, e in enumerate(paired)}
    for item in capture:
        kw = item["keyword"]
        entry = {
            "keyword": kw,
            "group": GROUPS.get(kw, item.get("group", "OTHER")),
            "response": item["response"],
        }
        if kw in index:
            paired[index[kw]] = entry
        else:
            paired.append(entry)
    SEARCH.write_text(json.dumps(paired, indent=2))
    print(f"Updated {len(capture)} keywords in search_responses.json")

if __name__ == "__main__":
    main()
