#!/usr/bin/env python3
"""
Run all keyword searches via Upwork MCP and append to _search_queue.jsonl.

Requires MCP bridge script at ./_mcp_call.js (uses agent socket) OR pre-populated
_batches/responses/<slug>.json files from hourly agent MCP runs.

This script is the durable runner: once responses exist, it builds the queue
and invokes _run_hourly.py.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
ORG = "1472686528932380673"
RESP_DIR = BASE / "_batches" / "responses"
QUEUE = BASE / "_search_queue.jsonl"
KEYWORDS = json.loads((BASE / "keywords.json").read_text())
MCP_JS = BASE / "_mcp_call.js"


def slug(kw: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", kw.lower()).strip("_")


def strip_job(j):
    j = dict(j)
    j.pop("description_snippet", None)
    return j


def call_find_jobs(query: str):
    if not MCP_JS.exists():
        return None
    proc = subprocess.run(
        ["node", str(MCP_JS), "upwork__find_jobs", json.dumps({
            "action": "search",
            "org_uid": ORG,
            "params": {"query": query, "sort": "recency", "limit": 10},
        })],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if proc.returncode != 0:
        return {"status": "error", "reason": proc.stderr or proc.stdout}
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"status": "error", "reason": "invalid json from mcp bridge"}


def append_queue(keyword, group, response):
    resp = response or {}
    if resp.get("status") == "error" or resp.get("error_code"):
        line = {
            "keyword": keyword,
            "group": group,
            "status": "error",
            "error": resp.get("reason") or resp.get("error_code"),
            "jobs": [],
        }
    else:
        jobs = [strip_job(j) for j in (resp.get("jobs") or [])]
        line = {"keyword": keyword, "group": group, "status": "ok", "jobs": jobs}
    with QUEUE.open("a") as f:
        f.write(json.dumps(line, ensure_ascii=False) + "\n")


def main():
    fresh = "--fresh-queue" in sys.argv
    if fresh:
        QUEUE.write_text("")

    missing = []
    for item in KEYWORDS:
        kw, group = item["keyword"], item["group"]
        path = RESP_DIR / f"{slug(kw)}.json"
        resp = None
        if path.exists():
            resp = json.loads(path.read_text())
        else:
            resp = call_find_jobs(kw)
            if resp is None:
                missing.append(kw)
                continue
            if resp.get("status") == "ok":
                RESP_DIR.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(resp, ensure_ascii=False))
        append_queue(kw, group, resp)

    if missing:
        print("Missing MCP responses for:", ", ".join(missing), file=sys.stderr)
        sys.exit(2)

    subprocess.check_call([sys.executable, str(BASE / "_run_hourly.py")])


if __name__ == "__main__":
    main()
