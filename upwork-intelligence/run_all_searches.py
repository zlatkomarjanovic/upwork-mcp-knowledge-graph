#!/usr/bin/env python3
"""
Run all keyword searches via Upwork MCP and append to _batch_results.jsonl.

Requires Cursor agent runtime: invokes CallDynamicTool through the agent tool bridge
when CURSOR_AGENT=1 by writing request files and waiting on responses.

If bridge unavailable, exits with code 2 so the hourly agent can search via MCP directly.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent
KEYWORDS = BASE / "keywords.json"
ORG = "1472686528932380673"
BRIDGE = os.environ.get("UPWORK_MCP_BRIDGE", "http://127.0.0.1:0/mcp")


def slim_jobs(jobs):
    fields = (
        "url",
        "title",
        "published_date",
        "created_date",
        "job_type",
        "budget",
        "duration",
        "proposals_tier",
        "experience_level",
        "skills",
    )
    out = []
    for j in jobs or []:
        row = {k: j[k] for k in fields if k in j}
        row["client"] = j.get("client") or {}
        out.append(row)
    return out


def mcp_find_jobs(keyword: str):
    payload = {
        "namespace": "Upwork",
        "toolName": "upwork__find_jobs",
        "arguments": {
            "action": "search",
            "org_uid": ORG,
            "params": {"query": keyword, "sort": "recency", "limit": 10},
        },
    }
    req = urllib.request.Request(
        BRIDGE,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.load(resp)


def append_row(row):
    out = BASE / "_batch_results.jsonl"
    with out.open("a") as f:
        f.write(json.dumps(row, separators=(",", ":")) + "\n")


def main():
    kws = json.loads(KEYWORDS.read_text())
    errors = []
    for i, item in enumerate(kws):
        kw = item["keyword"]
        group = item["group"]
        try:
            mcp = mcp_find_jobs(kw)
            if mcp.get("status") == "error" or mcp.get("error_code"):
                append_row(
                    {
                        "keyword": kw,
                        "group": group,
                        "error": mcp.get("reason") or mcp.get("error_code"),
                    }
                )
                errors.append(kw)
            else:
                append_row(
                    {
                        "keyword": kw,
                        "group": group,
                        "jobs": slim_jobs(mcp.get("jobs")),
                    }
                )
        except (urllib.error.URLError, OSError, json.JSONDecodeError) as e:
            print(f"Bridge unavailable at {kw}: {e}", file=sys.stderr)
            sys.exit(2)
        if (i + 1) % 10 == 0:
            time.sleep(0.2)
    print(f"Completed {len(kws)} keywords, errors: {len(errors)}")


if __name__ == "__main__":
    main()
