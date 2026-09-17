#!/usr/bin/env python3
"""Save slim MCP find_jobs response for one keyword."""
import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
RAW = BASE / "mcp_raw"
RAW.mkdir(exist_ok=True)

KEEP = (
    "url",
    "title",
    "job_type",
    "budget",
    "duration",
    "proposals_tier",
    "published_date",
    "created_date",
    "experience_level",
    "skills",
    "description_snippet",
    "client",
)


def slug(k: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", k.lower()).strip("-") or "kw"


def slim_job(j):
    return {k: j.get(k) for k in KEEP if k in j}


def main():
    keyword = sys.argv[1]
    raw = json.loads(Path(sys.argv[2]).read_text() if len(sys.argv) > 2 else sys.stdin.read())
    out = {
        "status": raw.get("status", "ok"),
        "jobs": [slim_job(j) for j in (raw.get("jobs") or [])],
    }
    if raw.get("error"):
        out["error"] = raw["error"]
    (RAW / f"{slug(keyword)}.json").write_text(json.dumps(out, ensure_ascii=False))
    print(keyword, "ok", len(out["jobs"]))


if __name__ == "__main__":
    main()
