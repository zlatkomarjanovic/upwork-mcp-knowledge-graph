#!/usr/bin/env python3
"""
UPWORK_MCP_CMD bridge: JSON-RPC stdin/stdout for upwork__find_jobs search only.
Uses pre-filled mcp_queue/{slug}.json when present; otherwise returns empty ok.
Cloud agent should populate mcp_queue via save_mcp_queue.py after live MCP calls.
"""
import hashlib
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
QUEUE = BASE / "mcp_queue"
CACHE = BASE / "mcp_cache.json"


def slug(kw):
    return hashlib.md5(kw.encode()).hexdigest()[:12]


def main():
    raw = sys.stdin.read()
    if not raw.strip():
        return
    req = json.loads(raw)
    args = req.get("params", {}).get("arguments", {})
    query = (args.get("params") or {}).get("query", "")
    resp = None
    if CACHE.exists():
        cache = json.loads(CACHE.read_text())
        if query in cache:
            resp = cache[query]
    if resp is None:
        qf = QUEUE / f"{slug(query)}.json"
        if qf.exists():
            data = json.loads(qf.read_text())
            resp = data.get("response") or data
    if resp is None:
        raw_path = BASE / "raw_batches" / f"{slug(query)}.json"
        if raw_path.exists():
            data = json.loads(raw_path.read_text())
            resp = data.get("response") or data
    if resp is None and CACHE.exists():
        cache = json.loads(CACHE.read_text())
        if query in cache:
            resp = cache[query]
    if resp is None:
        resp = {"status": "ok", "jobs": []}
    out = {
        "jsonrpc": "2.0",
        "id": req.get("id", 1),
        "result": {
            "content": [{"type": "text", "text": json.dumps(resp)}],
        },
    }
    sys.stdout.write(json.dumps(out))


if __name__ == "__main__":
    main()
