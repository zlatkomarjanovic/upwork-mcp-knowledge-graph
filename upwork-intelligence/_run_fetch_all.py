#!/usr/bin/env python3
"""
Fetch all keywords via Upwork MCP (Cloud Agent).

In Cloud Agent runs, invoke this script AFTER appending MCP results to
_search_queue.jsonl using _add_searches.py, OR extend this script once a
local MCP bridge is available.

Then merges queue and runs _process_run.py.
"""
import json
import subprocess
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent
ORG = "1472686528932380673"
RAW = BASE / "_raw_run.json"
QUEUE = BASE / "_search_queue.jsonl"
KEYWORDS = json.loads((BASE / "_keywords_all.json").read_text())
PAUSE_SEC = 5.5


def slim_job(j):
    fields = (
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
    )
    return {k: j.get(k) for k in fields}


def slim(resp):
    if resp.get("status") == "error" or resp.get("error_code"):
        return {
            "status": "error",
            "error_code": resp.get("error_code"),
            "reason": resp.get("reason"),
        }
    return {"status": "ok", "jobs": [slim_job(j) for j in resp.get("jobs") or []]}


def merge_queue():
    if not QUEUE.exists() or not QUEUE.read_text().strip():
        return 0
    raw = json.loads(RAW.read_text())
    done = {s["keyword"] for s in raw["searches"]}
    added = 0
    for line in QUEUE.read_text().splitlines():
        if not line.strip():
            continue
        entry = json.loads(line)
        kw = entry.get("keyword")
        if not kw or kw in done:
            continue
        raw["searches"].append(entry)
        done.add(kw)
        added += 1
    raw["meta"]["keywordsCompleted"] = len(raw["searches"])
    RAW.write_text(json.dumps(raw))
    if added:
        QUEUE.write_text("")
    return added


def call_find_jobs(keyword):
    try:
        from cursor_dynamic_tools import call_dynamic_tool  # type: ignore
    except ImportError:
        return {
            "status": "error",
            "error_code": "NO_MCP_BRIDGE",
            "reason": "Append MCP results to _search_queue.jsonl from the agent",
        }
    return call_dynamic_tool(
        namespace="Upwork",
        toolName="upwork__find_jobs",
        arguments={
            "action": "search",
            "org_uid": ORG,
            "params": {"query": keyword, "sort": "recency", "limit": 10},
        },
    )


def fetch_all():
    raw = json.loads(RAW.read_text())
    done = {s["keyword"] for s in raw["searches"]}
    pending = [k for k in KEYWORDS if k not in done]
    for i, kw in enumerate(pending):
        resp = call_find_jobs(kw)
        raw["searches"].append({"keyword": kw, "response": slim(resp)})
        raw["meta"]["keywordsCompleted"] = len(raw["searches"])
        RAW.write_text(json.dumps(raw))
        if i + 1 < len(pending):
            time.sleep(PAUSE_SEC)


def main():
    merge_queue()
    raw = json.loads(RAW.read_text())
    if len(raw["searches"]) < len(KEYWORDS):
        fetch_all()
    subprocess.check_call([sys.executable, str(BASE / "_process_run.py")])


if __name__ == "__main__":
    main()
