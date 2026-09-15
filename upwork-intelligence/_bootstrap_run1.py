#!/usr/bin/env python3
"""Bootstrap run 1 from collected MCP search payloads (2h window)."""
import json
import subprocess
from pathlib import Path

BASE = Path(__file__).resolve().parent
# Raw queue lines: keyword, group, jobs list (minimal fields preserved)
BATCHES = BASE / "bootstrap_batches.json"
if not BATCHES.exists():
    raise SystemExit("bootstrap_batches.json missing")

data = json.loads(BATCHES.read_text())
queue = BASE / "_search_queue.jsonl"
with queue.open("w") as f:
    for item in data:
        f.write(
            json.dumps(
                {
                    "keyword": item["keyword"],
                    "group": item["group"],
                    "status": "ok" if item.get("jobs") is not None else "error",
                    "jobs": item.get("jobs") or [],
                    "error": item.get("error"),
                }
            )
            + "\n"
        )

subprocess.check_call(["python3", str(BASE / "_run_hourly.py")])
