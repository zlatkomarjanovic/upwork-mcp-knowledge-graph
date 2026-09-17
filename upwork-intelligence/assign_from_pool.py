#!/usr/bin/env python3
"""Build _batch_results.jsonl rows for all keywords from a shared job pool (fallback)."""
import json, re
from pathlib import Path

BASE = Path(__file__).parent
KW_FILE = BASE / "keywords.json"
POOL_FILE = BASE / "fresh_jobs_pool.json"
OUT = BASE / "_batch_results.jsonl"

def norm_url(url):
    if not url:
        return None
    return url.split("?")[0]

def match_jobs(keyword, pool, limit=10):
    words = [w for w in re.split(r"\W+", keyword.lower()) if len(w) > 1]
    if not words:
        return []
    hits = []
    for j in pool:
        blob = " ".join(
            [
                (j.get("title") or "").lower(),
                " ".join(j.get("skills") or []).lower(),
            ]
        )
        if all(w in blob for w in words if w not in {"and", "the", "for"}):
            hits.append(j)
    hits.sort(key=lambda x: x.get("published_date") or x.get("created_date") or "", reverse=True)
    return hits[:limit]

def main():
    keywords = json.loads(KW_FILE.read_text())
    pool = json.loads(POOL_FILE.read_text()) if POOL_FILE.exists() else []
    seen_urls = set()
    deduped = []
    for j in pool:
        u = norm_url(j.get("url"))
        if u and u not in seen_urls:
            seen_urls.add(u)
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
