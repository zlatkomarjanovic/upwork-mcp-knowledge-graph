#!/usr/bin/env python3
"""Persist MCP search batch responses to mcp_raw/."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "mcp_raw"
RAW.mkdir(parents=True, exist_ok=True)


def slim_job(job: dict) -> dict:
    out = {k: job.get(k) for k in (
        "url", "title", "job_type", "budget", "duration", "proposal_count",
        "published_date", "created_date", "experience_level", "skills", "client",
        "description_snippet",
    )}
    if out.get("description_snippet"):
        out["description_snippet"] = out["description_snippet"][:200]
    return out


def slim_item(item: dict) -> dict:
    resp = item.get("response") or item
    jobs = resp.get("jobs") or []
    return {
        "keyword": item.get("keyword"),
        "group": item.get("group"),
        "response": {
            "status": resp.get("status", "ok"),
            "jobs": [slim_job(j) for j in jobs],
        },
    }


def main():
    if len(sys.argv) > 1:
        data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    else:
        data = json.load(sys.stdin)
    if not isinstance(data, list):
        data = [data]
    for item in data:
        item = slim_item(item)
        kw = item.get("keyword", "unknown")
        safe = "".join(c if c.isalnum() else "_" for c in kw)[:80]
        path = RAW / f"{safe}.json"
        path.write_text(json.dumps(item, ensure_ascii=False), encoding="utf-8")
    print(f"saved {len(data)} keyword responses")


if __name__ == "__main__":
    main()
