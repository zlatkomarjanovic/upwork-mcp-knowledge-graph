#!/usr/bin/env python3
"""Rebuild search_responses.json from prior snapshot + in-window job injection."""
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).parent
GROUPS = json.loads((ROOT / "keywords.json").read_text())["keywords"]
SEARCH = ROOT / "search_responses.json"
ANCHOR = datetime.now(timezone.utc)
WINDOW = timedelta(hours=1)


def in_window(pub: str | None) -> bool:
    if not pub:
        return False
    dt = datetime.fromisoformat(pub.replace("Z", "+00:00"))
    return ANCHOR - WINDOW <= dt <= ANCHOR


def slim_job(j: dict) -> dict:
    return {k: v for k, v in j.items() if k != "description_snippet"}


def main():
    paired = json.loads(SEARCH.read_text())
    # Collect all jobs from snapshot, keep in-window only
    all_jobs: dict[str, dict] = {}
    for entry in paired:
        for j in (entry.get("response") or {}).get("jobs") or []:
            u = j.get("url", "").split("?")[0]
            if u and in_window(j.get("published_date") or j.get("created_date")):
                all_jobs[u] = slim_job(j)
    # Rebuild each keyword response from original search jobs filtered to window
    out = []
    for kw, group in GROUPS.items():
        orig = next((e for e in paired if e["keyword"] == kw), None)
        jobs = []
        if orig:
            for j in (orig.get("response") or {}).get("jobs") or []:
                if in_window(j.get("published_date") or j.get("created_date")):
                    jobs.append(slim_job(j))
        out.append({"keyword": kw, "group": group, "response": {"status": "ok", "jobs": jobs}})
    SEARCH.write_text(json.dumps(out, indent=2))
    print(json.dumps({"keywords": len(out), "unique_in_window": len(all_jobs)}, indent=2))


if __name__ == "__main__":
    main()
