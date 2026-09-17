#!/usr/bin/env python3
"""Rebuild search_responses.json job lists from fresh_jobs_pool.json per keyword (text match)."""
import json
import re
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


def job_text(j: dict) -> str:
    return " ".join(
        [
            j.get("title") or "",
            " ".join(j.get("skills") or []),
            j.get("budget") or "",
        ]
    ).lower()


def kw_tokens(kw: str) -> list[str]:
    return [t for t in re.split(r"[^a-z0-9]+", kw.lower()) if len(t) > 2]


def matches(kw: str, j: dict) -> bool:
    text = job_text(j)
    toks = kw_tokens(kw)
    if not toks:
        return False
    hits = sum(1 for t in toks if t in text)
    if hits >= max(1, len(toks) // 2):
        return True
    if "ghl" in kw.lower() and "highlevel" in text:
        return True
    if kw.lower() == "GHL".lower() and "highlevel" in text:
        return True
    return False


def main() -> None:
    pool = [j for j in json.loads(POOL.read_text()) if in_window(j.get("published_date") or j.get("created_date"))]
    out = []
    for kw, group in GROUPS.items():
        jobs = [j for j in pool if matches(kw, j)]
        out.append({"keyword": kw, "group": group, "response": {"status": "ok", "jobs": jobs}})
    SEARCH.write_text(json.dumps(out, indent=2))
    print(json.dumps({"keywords": len(out), "pool_in_window": len(pool)}, indent=2))


if __name__ == "__main__":
    main()
