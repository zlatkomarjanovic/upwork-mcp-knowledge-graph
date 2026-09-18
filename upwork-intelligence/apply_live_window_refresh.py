#!/usr/bin/env python3
"""Filter each keyword response in search_responses.json to jobs in the live window."""
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).parent
SEARCH = ROOT / "search_responses.json"
WINDOW_H = 2.0
ANCHOR = datetime.now(timezone.utc)


def in_window(pub: str | None) -> bool:
    if not pub:
        return False
    dt = datetime.fromisoformat(pub.replace("Z", "+00:00"))
    age = (ANCHOR - dt).total_seconds()
    return 0 <= age <= WINDOW_H * 3600


def slim(j: dict) -> dict:
    return {k: v for k, v in j.items() if k != "description_snippet"}


def main() -> None:
    paired = json.loads(SEARCH.read_text())
    kept = 0
    for entry in paired:
        jobs = []
        for j in (entry.get("response") or {}).get("jobs") or []:
            if in_window(j.get("published_date") or j.get("created_date")):
                jobs.append(slim(j))
                kept += 1
        entry["response"] = {"status": "ok", "jobs": jobs}
    SEARCH.write_text(json.dumps(paired, ensure_ascii=False))
    print(json.dumps({"keywords": len(paired), "jobs_in_window": kept}))


if __name__ == "__main__":
    main()
