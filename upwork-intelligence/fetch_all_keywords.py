#!/usr/bin/env python3
"""Fetch all keywords via sequential Upwork MCP calls (for cron / manual run).

Requires running inside Cursor Cloud Agent with Upwork MCP authenticated.
Uses cursor dynamic tool bridge when CURSOR_MCP_BRIDGE is set; otherwise
expects pre-populated raw_search_results.json from agent MCP batch runs.
"""
import json
import subprocess
import sys
import time
from pathlib import Path

BASE = Path(__file__).parent
KEYWORDS = json.loads((BASE / "keywords.json").read_text())["keywords"]
ORG = json.loads((BASE / "keywords.json").read_text())["org_uid"]
RAW = BASE / "raw_search_results.json"
DELAY = 5.5  # stay under ~12 req/min


def mcp_search(keyword: str) -> dict:
    payload = {
        "namespace": "Upwork",
        "toolName": "upwork__find_jobs",
        "arguments": {
            "action": "search",
            "org_uid": ORG,
            "params": {"query": keyword, "sort": "recency", "limit": 10},
        },
    }
    cmd = ["python3", str(BASE / "_mcp_call.py"), json.dumps(payload)]
    out = subprocess.check_output(cmd, text=True)
    return json.loads(out)


def main():
    data = {"searches": [], "errors": []}
    if RAW.exists():
        data = json.loads(RAW.read_text())
    done = {s["keyword"] for s in data.get("searches", [])}
    for kw in KEYWORDS:
        if kw in done:
            continue
        try:
            resp = mcp_search(kw)
            if resp.get("status") == "error":
                data["errors"].append(kw)
            else:
                data["searches"].append({"keyword": kw, "response": resp})
        except Exception:
            data["errors"].append(kw)
        RAW.write_text(json.dumps(data, indent=2))
        time.sleep(DELAY)
    print(json.dumps({"searches": len(data["searches"]), "errors": len(data["errors"])}))


if __name__ == "__main__":
    main()
