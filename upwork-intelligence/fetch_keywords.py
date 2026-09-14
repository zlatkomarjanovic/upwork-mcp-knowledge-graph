#!/usr/bin/env python3
"""Sequential Upwork keyword fetch via Cursor MCP bridge (stdio JSON lines).

Usage (from repo root, with MCP bridge wired):
  python3 upwork-intelligence/fetch_keywords.py

This script is optional for unattended runs; the hourly agent may call Upwork MCP directly.
"""
import json
import subprocess
import sys
import time
from pathlib import Path

ORG = "1472686528932380673"
ROOT = Path(__file__).resolve().parent
KEYWORDS = json.loads((ROOT / "keywords.json").read_text())
OUT = ROOT / "search_responses.json"
INTERVAL = 6.0


def call_find_jobs(title: str) -> dict:
    payload = {
        "action": "search",
        "org_uid": ORG,
        "params": {"title": title, "sort": "recency", "limit": 10},
    }
    proc = subprocess.run(
        [sys.executable, str(ROOT / "_mcp_call.py"), "upwork__find_jobs", json.dumps(payload)],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return {"error": proc.stderr.strip() or proc.stdout.strip()}
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"error": proc.stdout[:500]}


def main() -> None:
    existing = json.loads(OUT.read_text()) if OUT.exists() else []
    done = {e.get("keyword") for e in existing if not e.get("error")}
    results = list(existing)
    for item in KEYWORDS:
        kw = item["keyword"]
        if kw in done:
            continue
        resp = call_find_jobs(item["title"])
        entry = {
            "keyword": kw,
            "group": item["group"],
            "jobs": resp.get("jobs", []),
            "error": resp.get("error") or resp.get("error_code"),
        }
        results.append(entry)
        OUT.write_text(json.dumps(results, ensure_ascii=False))
        time.sleep(INTERVAL)
    print(json.dumps({"total": len(results), "path": str(OUT)}))


if __name__ == "__main__":
    main()
