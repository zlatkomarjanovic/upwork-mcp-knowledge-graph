#!/usr/bin/env python3
"""Invoke Upwork find_jobs via Cursor dynamic MCP (cloud agent only).

Usage: python3 _mcp_call.py '<json-payload>'

Payload shape:
{"namespace":"Upwork","toolName":"upwork__find_jobs","arguments":{...}}

When not running inside an agent turn, exits with code 2.
"""
from __future__ import annotations

import json
import sys


def main() -> None:
    if len(sys.argv) < 2:
        print("missing payload", file=sys.stderr)
        sys.exit(1)
    _ = json.loads(sys.argv[1])
    print(
        json.dumps(
            {
                "status": "error",
                "error_code": "NO_MCP_BRIDGE",
                "message": "Shell cannot call MCP; agent must use CallDynamicTool or populate cache/*.json",
            }
        )
    )
    sys.exit(2)


if __name__ == "__main__":
    main()
