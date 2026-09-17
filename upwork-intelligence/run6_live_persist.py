#!/usr/bin/env python3
"""Persist live MCP search results collected this run (compact). Then run .run_process.py."""
import json
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent

# Compact snapshots from live Upwork MCP searches (2026-09-17 ~02:00 UTC)
LIVE = json.loads((BASE / "run6_live_responses.json").read_text())


def main():
    for item in LIVE:
        kw = item["keyword"]
        group = item["group"]
        resp = item["response"]
        subprocess.run(
            [sys.executable, str(BASE / "persist_kw.py"), kw, group],
            input=json.dumps(resp),
            text=True,
            check=True,
            cwd=str(BASE),
        )
    subprocess.run([sys.executable, str(BASE / ".run_process.py")], check=True, cwd=str(BASE))


if __name__ == "__main__":
    main()
