#!/usr/bin/env python3
"""Append compact search batch to search_log.jsonl. Input: {keyword: mcp_response, ...}"""
import json
import sys
from pathlib import Path

LOG = Path(__file__).parent / "search_log.jsonl"


def compact(resp):
    if resp.get("status") == "error":
        return resp
    jobs = []
    for j in resp.get("jobs") or []:
        jobs.append(
            {
                "url": j.get("url"),
                "title": j.get("title"),
                "published_date": j.get("published_date"),
                "created_date": j.get("created_date"),
                "job_type": j.get("job_type"),
                "budget": j.get("budget"),
                "duration": j.get("duration"),
                "proposal_count": j.get("proposal_count"),
                "experience_level": j.get("experience_level"),
                "skills": j.get("skills"),
                "description_snippet": (j.get("description_snippet") or "")[:400],
                "client": j.get("client"),
            }
        )
    return {"status": resp.get("status", "ok"), "jobs": jobs}


def main():
    data = json.loads(Path(sys.argv[1]).read_text())
    with LOG.open("a") as f:
        for kw, resp in data.items():
            f.write(json.dumps({"kw": kw, "result": compact(resp)}, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    main()
