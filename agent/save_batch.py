#!/usr/bin/env python3
"""Save multiple search results to agent/partial/*.json. Input: JSON array of {keyword, group, response}."""
import json
import sys
from pathlib import Path

import record_search

PARTIAL = Path(__file__).resolve().parent / "partial"


def main():
    batch = json.loads(sys.stdin.read())
    for item in batch:
        kw = item["keyword"]
        group = item["group"]
        resp = item.get("response") or item
        jobs = resp.get("jobs", []) if isinstance(resp, dict) else []
        if resp.get("status") == "error":
            continue
        entry = {"keyword": kw, "group": group, "jobs": jobs}
        out = PARTIAL / f"{record_search.slug(kw)}.json"
        PARTIAL.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(entry, indent=2))
    print("saved", len(batch), "to", PARTIAL)


if __name__ == "__main__":
    main()
