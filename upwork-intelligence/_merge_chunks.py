#!/usr/bin/env python3
"""Merge _chunks/*.json into _raw_searches.json and run processor."""
import json
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).parent
CHUNKS = BASE / "_chunks"
OUT = BASE / "_raw_searches.json"


def main():
    searches = []
    errors = []
    for p in sorted(CHUNKS.glob("*.json")):
        data = json.loads(p.read_text())
        searches.extend(data.get("searches", []))
        errors.extend(data.get("errors", []))
    completed = sum(1 for s in searches if not s.get("error"))
    payload = {
        "runAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "keywordsAttempted": 93,
        "keywordsCompleted": completed,
        "searches": searches,
        "errors": errors,
    }
    OUT.write_text(json.dumps(payload))
    import _search_runner

    _search_runner.main()


if __name__ == "__main__":
    main()
