#!/usr/bin/env python3
"""Save one MCP find_jobs JSON response: save_mcp_raw.py KEYWORD < response.json"""
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent / "mcp_raw"


def slug(k: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in k).strip("_")[:120]


def main():
    kw = sys.argv[1]
    resp = json.load(sys.stdin)
    BASE.mkdir(parents=True, exist_ok=True)
    (BASE / f"{slug(kw)}.json").write_text(json.dumps(resp), encoding="utf-8")


if __name__ == "__main__":
    main()
