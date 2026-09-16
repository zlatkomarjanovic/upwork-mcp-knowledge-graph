#!/usr/bin/env python3
"""Bridge for fetch_all_keywords.py — invoke Upwork find_jobs via Cursor dynamic tools HTTP API."""
import json
import os
import sys
import urllib.request

SOCK = os.environ.get("CURSOR_AGENT_SOCKET", "/run/cursor/api.sock")


def call_tool(payload: dict) -> dict:
    body = json.dumps(
        {
            "namespace": payload.get("namespace"),
            "toolName": payload.get("toolName"),
            "arguments": payload.get("arguments", {}),
        }
    ).encode()
    req = urllib.request.Request(
        "http://localhost/v1/dynamic-tool/call",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raw = e.read().decode() if e.fp else str(e)
        return {"status": "error", "error": raw}


def main():
    payload = json.loads(sys.argv[1])
    print(json.dumps(call_tool(payload)))


if __name__ == "__main__":
    main()
