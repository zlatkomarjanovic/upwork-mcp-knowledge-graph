#!/usr/bin/env python3
"""Append unique MCP jobs from stdin JSON [{keyword, response}] into fresh_jobs_pool.json."""
import json
import sys
from pathlib import Path

POOL = Path(__file__).parent / "fresh_jobs_pool.json"


def main() -> None:
    batch = json.loads(sys.stdin.read())
    pool: list = json.loads(POOL.read_text()) if POOL.exists() else []
    seen = {j.get("id") for j in pool if j.get("id")}
    added = 0
    for item in batch:
        resp = item.get("response") or item.get("mcp") or {}
        for j in resp.get("jobs") or []:
            jid = j.get("id")
            if jid and jid not in seen:
                pool.append({k: v for k, v in j.items() if k != "description_snippet"})
                seen.add(jid)
                added += 1
    POOL.write_text(json.dumps(pool, ensure_ascii=False))
    print(len(pool), "pool", added, "added")


if __name__ == "__main__":
    main()
