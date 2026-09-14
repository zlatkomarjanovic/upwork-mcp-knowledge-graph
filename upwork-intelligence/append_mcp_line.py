#!/usr/bin/env python3
"""Append one {keyword, response} JSON line and update cache file."""
import json
import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).parent
CACHE = ROOT / "cache"
CACHE.mkdir(exist_ok=True)


def slim(resp: dict) -> dict:
    jobs = [{k: j[k] for k in j if k != "description_snippet"} for j in resp.get("jobs") or []]
    out = {"status": resp.get("status", "ok"), "jobs": jobs}
    for k in ("error_code", "error"):
        if k in resp:
            out[k] = resp[k]
    return out


def main() -> None:
    item = json.loads(sys.stdin.read())
    kw = item["keyword"]
    path = CACHE / (quote(kw, safe="") + ".json")
    path.write_text(json.dumps({"keyword": kw, "response": slim(item["response"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
