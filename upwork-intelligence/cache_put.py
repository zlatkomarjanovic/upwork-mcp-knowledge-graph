#!/usr/bin/env python3
"""Merge MCP responses into mcp_cache.json. stdin: object or array of {keyword, response}."""
import json
import sys
from pathlib import Path

CACHE = Path(__file__).resolve().parent / "mcp_cache.json"


def main():
    raw = json.load(sys.stdin)
    items = raw if isinstance(raw, list) else [raw]
    cache = {}
    if CACHE.exists():
        cache = json.loads(CACHE.read_text())
    for item in items:
        kw = item.get("keyword")
        if not kw:
            continue
        cache[kw] = item.get("response") or item
    CACHE.write_text(json.dumps(cache, ensure_ascii=False))
    print(len(cache))


if __name__ == "__main__":
    main()
