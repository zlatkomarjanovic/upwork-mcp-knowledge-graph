#!/usr/bin/env python3
"""Persist live MCP responses passed as JSON file list of {keyword, group, response}."""
import json
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent


def main():
    path = Path(sys.argv[1])
    items = json.loads(path.read_text())
    for item in items:
        subprocess.run(
            [sys.executable, str(BASE / "persist_kw.py"), item["keyword"], item["group"]],
            input=json.dumps(item["response"]),
            text=True,
            check=True,
        )
    print(len(items))


if __name__ == "__main__":
    main()
