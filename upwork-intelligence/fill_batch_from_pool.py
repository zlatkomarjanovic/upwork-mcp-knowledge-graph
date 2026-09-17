#!/usr/bin/env python3
"""Write one _batch_results.jsonl row per keyword using pool keyword matching."""
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
    lines = []
    for k in keywords:
        kw = k["keyword"]
        jobs = match_jobs(kw, pool)
        lines.append(json.dumps({"keyword": kw, "response": {"status": "ok", "jobs": jobs}}, ensure_ascii=False))
    OUT.write_text("\n".join(lines) + "\n")
    print(len(lines), "keywords", len(pool), "pool jobs")

if __name__ == "__main__":
    main()
