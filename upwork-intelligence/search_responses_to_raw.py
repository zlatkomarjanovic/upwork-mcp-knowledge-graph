#!/usr/bin/env python3
"""Convert search_responses.json to raw_batches/*.json for .run_process.py."""
import json
from pathlib import Path

BASE = Path(__file__).parent
SEARCH = BASE / "search_responses.json"
RAW = BASE / "raw_batches"
RAW.mkdir(exist_ok=True)


def main():
    paired = json.loads(SEARCH.read_text())
    for entry in paired:
        kw = entry["keyword"]
        group = entry.get("group", "OTHER")
        resp = entry.get("response") or {}
        slug = __import__("re").sub(r"[^a-z0-9]+", "_", kw.lower()).strip("_")[:80]
        if resp.get("error"):
            payload = {"keyword": kw, "group": group, "error": resp.get("error")}
        else:
            payload = {"keyword": kw, "group": group, "jobs": resp.get("jobs") or []}
        (RAW / f"{slug}.json").write_text(json.dumps(payload, ensure_ascii=False))
    print(len(list(RAW.glob("*.json"))))


if __name__ == "__main__":
    main()
