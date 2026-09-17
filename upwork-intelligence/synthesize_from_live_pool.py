#!/usr/bin/env python3
"""Build search_responses.json from merged live MCP pool (2h window) with keyword relevance filter."""
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent
RUN_AT = datetime(2026, 9, 17, 5, 49, 35, tzinfo=timezone.utc)
CUTOFF = RUN_AT.timestamp() - 2 * 3600
KW = json.loads((ROOT / "keywords.json").read_text())["keywords"]

# Slim jobs captured from live Upwork MCP searches this run (2h window).
POOL = json.loads((ROOT / "live_job_pool.json").read_text())


def in_window(job: dict) -> bool:
    posted = job.get("published_date") or job.get("created_date")
    if not posted:
        return False
    ts = datetime.fromisoformat(posted.replace("Z", "+00:00")).timestamp()
    return ts >= CUTOFF


def relevant(job: dict, keyword: str) -> bool:
    text = " ".join(
        [
            job.get("title") or "",
            " ".join(job.get("skills") or []),
            job.get("description_snippet") or "",
        ]
    ).lower()
    kw = keyword.lower()
    tokens = [t for t in re.split(r"[^a-z0-9.+]+", kw) if len(t) > 2]
    if not tokens:
        return kw in text
    hits = sum(1 for t in tokens if t in text)
    return hits >= max(1, len(tokens) // 2)


def main() -> None:
    pool = [j for j in POOL if in_window(j)]
    out = []
    for keyword, group in KW.items():
        jobs = [j for j in pool if relevant(j, keyword)]
        jobs = jobs[:10]
        slim = [{k: v for k, v in j.items() if k != "description_snippet"} for j in jobs]
        out.append({"keyword": keyword, "group": group, "response": {"status": "ok", "jobs": slim}})
    (ROOT / "search_responses.json").write_text(json.dumps(out, ensure_ascii=False))
    print(json.dumps({"pool": len(pool), "keywords": len(out)}))


if __name__ == "__main__":
    main()
