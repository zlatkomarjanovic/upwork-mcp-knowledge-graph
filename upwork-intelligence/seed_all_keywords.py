#!/usr/bin/env python3
"""Ensure _batch_results.jsonl has one row per configured keyword (pool-based fallback)."""
import json
from pathlib import Path

from assign_from_pool import match_jobs, norm_url

BASE = Path(__file__).parent
KW_FILE = BASE / "keywords.json"
POOL_FILE = BASE / "fresh_jobs_pool.json"
OUT = BASE / "_batch_results.jsonl"

def main():
    keywords = json.loads(KW_FILE.read_text())
    pool = json.loads(POOL_FILE.read_text()) if POOL_FILE.exists() else []
    seen = set()
    deduped = []
    for j in pool:
        u = norm_url(j.get("url"))
        if u and u not in seen:
            seen.add(u)
            deduped.append(j)
    pool = deduped

    existing = set()
    if OUT.exists():
        for line in OUT.read_text().splitlines():
            if line.strip():
                existing.add(json.loads(line).get("keyword"))

    with OUT.open("a", encoding="utf-8") as f:
        for k in keywords:
            kw = k["keyword"]
            if kw in existing:
                continue
            jobs = match_jobs(kw, pool)
            row = {"keyword": kw, "response": {"status": "ok", "jobs": jobs}}
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    main()
