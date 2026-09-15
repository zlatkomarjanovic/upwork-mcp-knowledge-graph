#!/usr/bin/env python3
"""Append one keyword search result to mcp_queue/. Usage: record_search.py <keyword> <group> <response.json>"""
import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
QUEUE = BASE / "mcp_queue"
QUEUE.mkdir(exist_ok=True)


def slug(kw: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", kw.lower()).strip("-")[:80]


def main():
    kw, group, resp_path = sys.argv[1], sys.argv[2], sys.argv[3]
    data = json.loads(Path(resp_path).read_text())
    entry = {"keyword": kw, "group": group}
    if data.get("status") != "ok" or data.get("error"):
        entry["error"] = data.get("error") or data.get("message") or "search_failed"
    else:
        jobs = []
        for j in data.get("jobs") or []:
            jobs.append(
                {
                    k: j[k]
                    for k in (
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
                    if k in j
                }
            )
        entry["jobs"] = jobs
    out = QUEUE / f"{slug(kw)}.json"
    out.write_text(json.dumps(entry, ensure_ascii=False))
    print(out.name, len(entry.get("jobs") or []), "jobs")


if __name__ == "__main__":
    main()
