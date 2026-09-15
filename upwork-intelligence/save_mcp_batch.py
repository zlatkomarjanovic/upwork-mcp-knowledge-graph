#!/usr/bin/env python3
"""Write MCP search results into upwork-intelligence/cache/."""
import json
import sys
from pathlib import Path
from urllib.parse import quote

from record_search import slim

ROOT = Path(__file__).parent
CACHE = ROOT / "cache"
CACHE.mkdir(exist_ok=True)


def main():
    batch = json.loads(sys.stdin.read())
    for item in batch:
        kw = item["keyword"]
        resp = slim(item["response"])
        path = CACHE / (quote(kw, safe="") + ".json")
        path.write_text(json.dumps({"keyword": kw, "response": resp}, ensure_ascii=False))
    print(len(list(CACHE.glob("*.json"))))


if __name__ == "__main__":
    main()
