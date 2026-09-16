#!/usr/bin/env python3
"""Fetch all keywords via Upwork MCP (Cursor dynamic tool HTTP). Used when api.sock works."""
import json
import subprocess
import sys
import time
from pathlib import Path

BASE = Path(__file__).parent
KEYWORDS = list(json.loads((BASE / "keywords.json").read_text())["keywords"].keys())
ORG = json.loads((BASE / "keywords.json").read_text())["org_uid"]
MCP = BASE / "_mcp_call.py"
CACHE = BASE / "mcp_cache"
CACHE.mkdir(exist_ok=True)


def search(kw: str) -> dict:
    payload = {
        "namespace": "Upwork",
        "toolName": "upwork__find_jobs",
        "arguments": {
            "action": "search",
            "org_uid": ORG,
            "params": {"query": kw, "sort": "recency", "limit": 10},
        },
    }
    out = subprocess.check_output(["python3", str(MCP), json.dumps(payload)], text=True)
    return json.loads(out)


def save(kw: str, resp: dict):
    from save_mcp_keyword import slim

    if resp.get("status") == "error":
        payload = {"keyword": kw, "error": True}
    else:
        payload = {"keyword": kw, "jobs": slim(resp)}
    slug = __import__("re").sub(r"[^a-z0-9]+", "_", kw.lower()).strip("_")
    (CACHE / f"{slug}.json").write_text(json.dumps(payload, ensure_ascii=False))


def main():
    errors = []
    for i, kw in enumerate(KEYWORDS):
        slug = __import__("re").sub(r"[^a-z0-9]+", "_", kw.lower()).strip("_")
        if (CACHE / f"{slug}.json").exists():
            continue
        try:
            resp = search(kw)
            save(kw, resp)
        except Exception:
            errors.append(kw)
        if i % 10 == 9:
            time.sleep(6)
    print(json.dumps({"done": len(list(CACHE.glob("*.json"))), "errors": errors}))


if __name__ == "__main__":
    main()
