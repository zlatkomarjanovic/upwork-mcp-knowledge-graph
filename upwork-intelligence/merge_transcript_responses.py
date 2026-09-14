#!/usr/bin/env python3
"""Overlay transcript find_jobs results onto search_responses; keep prior entry if missing."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent
from extract_transcript_searches import KEYWORDS, collect_find_jobs_by_keyword  # noqa: E402

SEARCH = ROOT / "search_responses.json"


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: merge_transcript_responses.py <transcript.json>", file=sys.stderr)
        sys.exit(1)
    data = json.loads(Path(sys.argv[1]).read_text())
    by_kw = collect_find_jobs_by_keyword(data)
    prior = {}
    if SEARCH.exists():
        for entry in json.loads(SEARCH.read_text()):
            prior[entry["keyword"]] = entry

    paired = []
    fresh = 0
    fallback = 0
    missing = []
    for spec in KEYWORDS:
        kw = spec["keyword"]
        if kw in by_kw:
            resp = by_kw[kw]
            fresh += 1
        elif kw in prior:
            resp = prior[kw].get("response") or {}
            fallback += 1
        else:
            resp = {"status": "error", "error_code": "MISSING_SEARCH"}
            missing.append(kw)
        paired.append({"keyword": kw, "group": spec["group"], "response": resp})

    SEARCH.write_text(json.dumps(paired, indent=2))
    print(json.dumps({"fresh": fresh, "fallback": fallback, "missing": len(missing), "missing_kw": missing[:20]}, indent=2))


if __name__ == "__main__":
    main()
