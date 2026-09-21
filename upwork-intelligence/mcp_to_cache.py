#!/usr/bin/env python3
"""Add one keyword response to mcp_cache.json: mcp_to_cache.py KEYWORD < response.json"""
import json
import sys
from pathlib import Path

CACHE = Path(__file__).resolve().parent / "mcp_cache.json"


def main():
    kw = sys.argv[1]
    resp = json.load(sys.stdin)
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    cache[kw] = resp
    CACHE.write_text(json.dumps(cache, ensure_ascii=False))
    print(len(cache))


if __name__ == "__main__":
    main()
