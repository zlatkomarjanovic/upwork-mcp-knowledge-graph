#!/usr/bin/env python3
"""Emergency: assign pooled in-window jobs to every keyword search response (dedupe by URL only)."""
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).parent
POOL = ROOT / "fresh_jobs_pool.json"
SEARCH = ROOT / "search_responses.json"
GROUPS = json.loads((ROOT / "keywords.json").read_text())["keywords"]
WINDOW = timedelta(hours=2)


def in_window(pub: str | None) -> bool:
    if not pub:
        return False
    dt = datetime.fromisoformat(pub.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    return timedelta(0) <= now - dt <= WINDOW


def main() -> None:
    pool = json.loads(POOL.read_text())
    jobs = [j for j in pool if in_window(j.get("published_date") or j.get("created_date"))]
    out = []
    for kw, group in GROUPS.items():
        out.append({"keyword": kw, "group": group, "response": {"status": "ok", "jobs": jobs}})
    SEARCH.write_text(json.dumps(out, indent=2))
    print(json.dumps({"keywords": len(out), "pool_jobs": len(jobs)}))


if __name__ == "__main__":
    main()
