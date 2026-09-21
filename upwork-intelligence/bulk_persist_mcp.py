#!/usr/bin/env python3
"""Persist all keywords from mcp_responses.jsonl (one {keyword, response} per line)."""
import json
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else BASE / "mcp_responses.jsonl"
    if not path.exists():
        print(json.dumps({"error": "missing", "path": str(path)}))
        sys.exit(2)
    n = 0
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        subprocess.run(
            [sys.executable, str(BASE / "agent_fetch_persist.py")],
            input=json.dumps(item),
            text=True,
            check=True,
            cwd=str(BASE),
        )
        n += 1
    print(json.dumps({"persisted": n}))


if __name__ == "__main__":
    main()
