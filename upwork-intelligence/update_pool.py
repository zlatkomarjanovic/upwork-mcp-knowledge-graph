#!/usr/bin/env python3
"""Merge jobs from MCP find_jobs JSON (stdin or file) into fresh_jobs_pool.json."""
import json, sys
from pathlib import Path

POOL = Path(__file__).parent / "fresh_jobs_pool.json"

def norm(u):
    return u.split("?")[0] if u else None

def load_mcp(path=None):
    if path:
        return json.loads(Path(path).read_text())
    return json.load(sys.stdin)

def main():
    src = sys.argv[1] if len(sys.argv) > 1 else None
    mcp = load_mcp(src)
    jobs = mcp.get("jobs") or []
    pool = json.loads(POOL.read_text()) if POOL.exists() else []
    seen = {norm(j.get("url")) for j in pool if j.get("url")}
    for j in jobs:
        u = norm(j.get("url"))
        if u and u not in seen:
            seen.add(u)
            pool.append(j)
    POOL.write_text(json.dumps(pool, ensure_ascii=False, indent=2))
    print(len(pool))

if __name__ == "__main__":
    main()
