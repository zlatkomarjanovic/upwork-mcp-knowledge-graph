#!/usr/bin/env python3
"""Ingest a JSON file [{keyword, response}] into mcp_cache/."""
import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).parent
CACHE = BASE / "mcp_cache"
CACHE.mkdir(exist_ok=True)


def slug(kw: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", kw.lower()).strip("_")


def slim_jobs(resp: dict) -> list:
    out = []
    for j in resp.get("jobs") or []:
        out.append({k: v for k, v in j.items() if k != "description_snippet"})
    return out


def main():
    path = Path(sys.argv[1])
    items = json.loads(path.read_text())
    for item in items:
        kw = item["keyword"]
        resp = item.get("response") or {}
        if resp.get("status") == "error" or item.get("error"):
            payload = {"keyword": kw, "error": True}
        else:
            payload = {"keyword": kw, "jobs": slim_jobs(resp)}
        (CACHE / f"{slug(kw)}.json").write_text(json.dumps(payload, ensure_ascii=False))
    print(json.dumps({"ingested": len(items), "cache_files": len(list(CACHE.glob("*.json")))}))


if __name__ == "__main__":
    main()
