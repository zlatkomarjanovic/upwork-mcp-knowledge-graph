#!/usr/bin/env python3
"""Append jobs from an MCP find_jobs response JSON file into fresh_jobs_pool.json."""
import json, sys
from pathlib import Path

POOL = Path(__file__).parent / "fresh_jobs_pool.json"

def norm(u):
    return u.split("?")[0] if u else None

def main():
    data = json.loads(Path(sys.argv[1]).read_text())
    jobs = data.get("jobs") or (data.get("response") or {}).get("jobs") or []
    pool = json.loads(POOL.read_text()) if POOL.exists() else []
    seen = {norm(j.get("url")) for j in pool if j.get("url")}
    for j in jobs:
        u = norm(j.get("url"))
        if u and u not in seen:
            seen.add(u)
            pool.append(j)
    POOL.write_text(json.dumps(pool, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
