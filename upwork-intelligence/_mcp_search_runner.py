#!/usr/bin/env python3
"""Run all keyword searches via Upwork MCP stdio bridge if UPWORK_MCP_CMD is set."""
import json
import os
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).parent
sys.path.insert(0, str(BASE))
from _process_run import KEYWORD_GROUPS  # noqa: E402

ORG = os.environ.get("UPWORK_ORG_UID", "1472686528932380673")
RAW = BASE / "search-results-raw.json"
INBOX = BASE / "mcp_inbox"


def slim_job(j):
    keys = (
        "url", "title", "description_snippet", "published_date", "created_date",
        "job_type", "budget", "duration", "proposal_count", "client",
        "experience_level", "skills",
    )
    return {k: j.get(k) for k in keys if k in j}


def load_inbox():
    entries = {}
    if not INBOX.is_dir():
        return entries
    for p in INBOX.glob("*.json"):
        data = json.loads(p.read_text())
        kw = data.get("keyword")
        if kw:
            entries[kw] = data
    return entries


def main():
    inbox = load_inbox()
    raw = {"searches": [], "errors": []}
    for group, kws in KEYWORD_GROUPS:
        for kw in kws:
            item = inbox.get(kw)
            if not item:
                raw["searches"].append({"keyword": kw, "group": group, "error": True})
                raw["errors"].append(kw)
                continue
            resp = item.get("response") or item
            if resp.get("status") != "ok" and item.get("error"):
                raw["searches"].append({"keyword": kw, "group": group, "error": True})
                raw["errors"].append(kw)
                continue
            jobs = [slim_job(j) for j in resp.get("jobs", [])]
            raw["searches"].append({"keyword": kw, "group": group, "jobs": jobs})
    RAW.write_text(json.dumps(raw))
    done = sum(1 for s in raw["searches"] if not s.get("error"))
    print(json.dumps({"stored": len(raw["searches"]), "completed": done, "errors": len(raw["errors"])}))


if __name__ == "__main__":
    main()
