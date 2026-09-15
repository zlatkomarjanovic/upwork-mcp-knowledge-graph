#!/usr/bin/env python3
"""Invoke Upwork find_jobs via Cursor agent MCP bridge (stdio JSON in/out)."""
import json
import socket
import sys

# Fallback: agent runs this with pre-serialized MCP payloads; when no bridge,
# print error JSON so fetch_all_keywords can record failures.
def main() -> None:
    payload = json.loads(sys.argv[1])
    # Unix-socket HTTP bridge is read-only meta-data only; MCP runs in agent context.
    print(json.dumps({"status": "error", "error_code": "NO_MCP_BRIDGE", "detail": payload.get("arguments", {}).get("params", {}).get("query")}))


if __name__ == "__main__":
    main()
