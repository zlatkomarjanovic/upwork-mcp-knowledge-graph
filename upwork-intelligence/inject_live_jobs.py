#!/usr/bin/env python3
"""Inject live MCP job rows into search_responses.json for process_run ingestion."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parent
SEARCH = ROOT / "search_responses.json"


def norm_url(url: str) -> str:
    return url.split("?")[0].rstrip("/") if url else ""


def slim_job(raw: dict) -> dict:
    return {k: v for k, v in raw.items() if k != "description_snippet"}


def main() -> None:
    jobs_path = ROOT / "incoming" / "live_jobs.json"
    if not jobs_path.exists():
        print("no live_jobs.json")
        return
    items = json.loads(jobs_path.read_text())
    paired = json.loads(SEARCH.read_text())
    by_kw = {e["keyword"]: e for e in paired}
    for item in items:
        kw = item["keyword"]
        raw = slim_job(item["job"])
        entry = by_kw.get(kw)
        if not entry:
            continue
        resp = entry.setdefault("response", {"status": "ok", "jobs": []})
        jobs = resp.setdefault("jobs", [])
        u = norm_url(raw.get("url", ""))
        if not u:
            continue
        if not any(norm_url(j.get("url", "")) == u for j in jobs):
            jobs.insert(0, raw)
    SEARCH.write_text(json.dumps(paired, indent=2))
    print(json.dumps({"injected": len(items)}))


if __name__ == "__main__":
    main()
