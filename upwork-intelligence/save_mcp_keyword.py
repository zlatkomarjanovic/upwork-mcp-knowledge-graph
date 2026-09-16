#!/usr/bin/env python3
"""Save one Upwork find_jobs response for a keyword into mcp_cache/."""
import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).parent
CACHE = BASE / "mcp_cache"
CACHE.mkdir(exist_ok=True)


def slug(kw: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", kw.lower()).strip("_")


def slim(resp: dict) -> list:
    jobs = []
    for j in resp.get("jobs") or []:
        jobs.append({k: v for k, v in j.items() if k != "description_snippet"})
    return jobs


def main():
    kw = sys.argv[1]
    resp = json.loads(sys.stdin.read())
    if resp.get("status") == "error":
        out = {"keyword": kw, "error": True}
    else:
        out = {"keyword": kw, "jobs": slim(resp)}
    (CACHE / f"{slug(kw)}.json").write_text(json.dumps(out, ensure_ascii=False))
    print(json.dumps({"keyword": kw, "jobs": len(out.get("jobs") or [])}))


if __name__ == "__main__":
    main()
