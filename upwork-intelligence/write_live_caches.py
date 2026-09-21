#!/usr/bin/env python3
"""Write cache/*.json for keywords patched this run (slim MCP snapshots)."""
import json
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).parent
CACHE = ROOT / "cache"
CACHE.mkdir(exist_ok=True)

# Snapshots from live Upwork MCP searches (2026-09-21 run), description_snippet omitted.
CACHES: dict[str, dict] = {}


def save(kw: str, resp: dict) -> None:
    jobs = [{k: v for k, v in j.items() if k != "description_snippet"} for j in resp.get("jobs") or []]
    slim = {"status": resp.get("status", "ok"), "jobs": jobs}
    if resp.get("hasMore") is not None:
        slim["hasMore"] = resp["hasMore"]
    path = CACHE / (quote(kw, safe="") + ".json")
    path.write_text(json.dumps({"keyword": kw, "response": slim}, ensure_ascii=False))


def main() -> None:
    for kw, resp in CACHES.items():
        save(kw, resp)
    print("wrote", len(CACHES), "cache files")


if __name__ == "__main__":
    main()
