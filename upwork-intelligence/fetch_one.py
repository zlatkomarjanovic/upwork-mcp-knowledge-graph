#!/usr/bin/env python3
"""Persist one MCP response: fetch_one.py KEYWORD GROUP < response.json"""
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent


def main():
    if len(sys.argv) < 3:
        sys.exit("usage: fetch_one.py KEYWORD GROUP")
    kw, group = sys.argv[1], sys.argv[2]
    resp = sys.stdin.read()
    subprocess.run(
        [sys.executable, str(BASE / "persist_kw.py"), kw, group],
        input=resp,
        text=True,
        check=True,
    )
    subprocess.run(
        [sys.executable, str(BASE / "cache_put.py")],
        input=f'{{"keyword": {repr(kw)}, "response": {resp}}}',
        text=True,
        check=True,
    )


if __name__ == "__main__":
    main()
