#!/usr/bin/env python3
"""Merge search result JSONL chunks and run _process_run.py. Agent appends to _search_chunks.jsonl."""
import json
from pathlib import Path

BASE = Path(__file__).parent
CHUNKS = BASE / "_search_chunks.jsonl"
RAW = BASE / "_raw_searches.json"
KW = json.loads((BASE / "_keywords.json").read_text())


def main():
    searches = []
    errors = []
    if CHUNKS.exists():
        for line in CHUNKS.read_text().splitlines():
            if not line.strip():
                continue
            o = json.loads(line)
            searches.append(o)
            if o.get("error"):
                errors.append(o.get("keyword"))
    attempted = len(KW)
    completed = sum(1 for s in searches if not s.get("error"))
    missing = [k["keyword"] for k in KW if k["keyword"] not in {s.get("keyword") for s in searches}]
    for kw in missing:
        searches.append({"keyword": kw, "group": next(x["group"] for x in KW if x["keyword"] == kw), "error": "not_run_this_cycle", "jobs": []})
        errors.append(kw)
    raw = {
        "runAt": searches[0].get("runAt") if searches else None,
        "runNumber": searches[0].get("runNumber", 1) if searches else 1,
        "windowHours": 2,
        "searches": searches,
        "errors": errors,
    }
    RAW.write_text(json.dumps(raw))
    import _process_run

    _process_run.main()


if __name__ == "__main__":
    main()
