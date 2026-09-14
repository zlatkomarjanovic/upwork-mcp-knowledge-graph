#!/usr/bin/env python3
"""Write MCP search batch into cache/*.json for merge_cache.py."""
import json
import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).parent
CACHE = ROOT / "cache"
CACHE.mkdir(exist_ok=True)


def slim(resp: dict) -> dict:
    jobs = []
    for j in resp.get("jobs") or []:
        jobs.append({k: v for k, v in j.items() if k != "description_snippet"})
    out = {"status": resp.get("status", "ok"), "jobs": jobs}
    for k in ("error", "error_code"):
        if k in resp:
            out[k] = resp[k]
    return out


def main() -> None:
    batch = json.loads(sys.stdin.read())
    for item in batch:
        kw = item["keyword"]
        resp = slim(item.get("response") or {})
        path = CACHE / (quote(kw, safe="") + ".json")
        path.write_text(json.dumps({"keyword": kw, "response": resp}, ensure_ascii=False))
    print(len(list(CACHE.glob("*.json"))))


if __name__ == "__main__":
    main()
