#!/usr/bin/env python3
"""Invoke Upwork find_jobs via Cursor dynamic tool bridge (cloud agent only)."""
import json
import os
import sys
import urllib.request

BRIDGE = os.environ.get(
    "CURSOR_MCP_BRIDGE",
    "http://127.0.0.1:7942/mcp/Upwork/upwork__find_jobs",
)


def main() -> None:
    payload = json.loads(sys.argv[1])
    req = urllib.request.Request(
        BRIDGE,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            print(resp.read().decode())
    except Exception as e:
        print(json.dumps({"status": "error", "error": str(e)}))


if __name__ == "__main__":
    main()
