#!/usr/bin/env python3
"""Ingest a JSON file: [{keyword, group, response}, ...] into mcp_queue/."""
import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
QUEUE = BASE / "mcp_queue"
QUEUE.mkdir(exist_ok=True)

FIELDS = (
    "url",
    "title",
    "published_date",
    "created_date",
    "job_type",
    "budget",
    "duration",
    "proposal_count",
    "experience_level",
    "skills",
    "client",
    "description_snippet",
)


def slug(kw: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", kw.lower()).strip("-")[:80]


def main():
    chunk = json.loads(Path(sys.argv[1]).read_text())
    for item in chunk:
        kw = item["keyword"]
        group = item.get("group", "")
        resp = item.get("response") or {}
        entry = {"keyword": kw, "group": group}
        if resp.get("status") != "ok" or resp.get("error_code"):
            entry["error"] = resp.get("error_code") or resp.get("reason") or "search_failed"
        else:
            jobs = []
            for j in resp.get("jobs") or []:
                jobs.append({k: j[k] for k in FIELDS if k in j})
            entry["jobs"] = jobs
        (QUEUE / f"{slug(kw)}.json").write_text(json.dumps(entry, ensure_ascii=False))
    print("ingested", len(chunk), "keywords")


if __name__ == "__main__":
    main()
