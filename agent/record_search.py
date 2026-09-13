#!/usr/bin/env python3
"""Record one search: keyword, group, and Upwork find_jobs API response JSON file."""
import json
import re
import sys
from pathlib import Path

PARTIAL = Path(__file__).resolve().parent / "partial"


def slug(keyword: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", keyword.lower()).strip("_")
    return s[:80]


def main():
    keyword, group, resp_path = sys.argv[1], sys.argv[2], sys.argv[3]
    resp = json.loads(Path(resp_path).read_text())
    jobs = resp.get("jobs") if isinstance(resp, dict) else resp
    if jobs is None and isinstance(resp, dict) and "jobs" not in resp:
        jobs = []
    entry = {"keyword": keyword, "group": group, "jobs": jobs or []}
    PARTIAL.mkdir(parents=True, exist_ok=True)
    out = PARTIAL / f"{slug(keyword)}.json"
    out.write_text(json.dumps(entry, indent=2))
    print(out, len(entry["jobs"]))


if __name__ == "__main__":
    main()
