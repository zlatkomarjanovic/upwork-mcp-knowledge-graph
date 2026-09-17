#!/usr/bin/env python3
"""
Run all keyword searches via Upwork MCP JSON-RPC on Cursor's local MCP bridge.
Used by hourly automation when shell can reach the bridge; otherwise agent calls MCP directly.
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
RUN_DATA = BASE / "run_data.jsonl"
ORG = os.environ.get("UPWORK_ORG_UID", "1472686528932380673")

# Cursor cloud agents expose MCP over this bridge when UPWORK_MCP_URL is set.
MCP_URL = os.environ.get("UPWORK_MCP_URL", "")


def mcp_call(tool_name: str, arguments: dict) -> dict:
    if not MCP_URL:
        raise RuntimeError("UPWORK_MCP_URL not set")
    body = json.dumps(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
        }
    ).encode()
    req = urllib.request.Request(
        MCP_URL,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        payload = json.load(resp)
    if "error" in payload:
        raise RuntimeError(payload["error"])
    result = payload.get("result") or {}
    content = result.get("content") or []
    for block in content:
        if block.get("type") == "text":
            return json.loads(block["text"])
    return result


def search_keyword(keyword: str) -> dict:
    return mcp_call(
        "upwork__find_jobs",
        {
            "action": "search",
            "org_uid": ORG,
            "params": {"query": keyword, "sort": "recency", "limit": 10},
        },
    )


def main():
    if RUN_DATA.exists():
        RUN_DATA.write_text("")
    meta = json.loads(KEYWORDS.read_text())
    errors = []
    for i, row in enumerate(meta):
        kw, group = row["keyword"], row["group"]
        try:
            resp = search_keyword(kw)
            line = {"keyword": kw, "group": group, "jobs": resp.get("jobs") or []}
            if resp.get("status") != "ok" and not line["jobs"]:
                line = {"keyword": kw, "group": group, "error": resp.get("message", "search_failed")}
        except Exception as e:
            line = {"keyword": kw, "group": group, "error": str(e)}
            errors.append(kw)
        with RUN_DATA.open("a", encoding="utf-8") as f:
            f.write(json.dumps(line, ensure_ascii=False) + "\n")
        if (i + 1) % 10 == 0:
            time.sleep(1)
    print(json.dumps({"completed": len(meta) - len(errors), "errors": errors}))


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        sys.exit(2)
