#!/usr/bin/env python3
"""Prepend fresh jobs into search_responses.json for run 14."""
import json
from pathlib import Path

ROOT = Path(__file__).parent
SEARCH = ROOT / "search_responses.json"
PATCH = ROOT / "run14_new_jobs_raw.json"


def norm(url: str) -> str:
    return url.split("?")[0].rstrip("/")


def main():
    items = json.loads(PATCH.read_text())
    paired = json.loads(SEARCH.read_text())
    by_kw = {e["keyword"]: e for e in paired}
    for item in items:
        kw = item["keyword"]
        raw = item["raw"]
        url = norm(raw["url"])
        entry = by_kw.get(kw)
        if not entry:
            continue
        jobs = entry.setdefault("response", {}).setdefault("jobs", [])
        if any(norm(j.get("url") or "") == url for j in jobs):
            continue
        jobs.insert(0, raw)
    SEARCH.write_text(json.dumps(paired, indent=2))
    print("injected", len(items), "entries")


if __name__ == "__main__":
    main()
