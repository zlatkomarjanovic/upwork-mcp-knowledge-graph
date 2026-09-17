#!/usr/bin/env python3
"""Persist live MCP search batches to cache/ (stdin: JSON array of {keyword, mcp|response})."""
import json
import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).parent
CACHE = ROOT / "cache"
CACHE.mkdir(exist_ok=True)


def slim(resp: dict) -> dict:
    jobs = [{k: v for k, v in j.items() if k != "description_snippet"} for j in (resp.get("jobs") or [])]
    out = {"status": resp.get("status", "ok"), "jobs": jobs}
    for k in ("error_code", "error"):
        if k in resp:
            out[k] = resp[k]
    return out


def main() -> None:
    items = json.loads(sys.stdin.read())
    for item in items:
        kw = item["keyword"]
        resp = item.get("mcp") or item.get("response") or item
        path = CACHE / (quote(kw, safe="") + ".json")
        path.write_text(json.dumps({"keyword": kw, "response": slim(resp)}, ensure_ascii=False))
    print(len(items))


if __name__ == "__main__":
    main()
