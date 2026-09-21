#!/usr/bin/env python3
"""Append one MCP result and persist: append_response.py KEYWORD [GROUP] < response.json"""
import json
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: append_response.py KEYWORD [GROUP]")
    kw = sys.argv[1]
    group = sys.argv[2] if len(sys.argv) > 2 else None
    resp = json.load(sys.stdin)
    item = {"keyword": kw, "response": resp}
    if group:
        item["group"] = group
    with (BASE / "mcp_responses.jsonl").open("a") as f:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")
    subprocess.run(
        [sys.executable, str(BASE / "agent_fetch_persist.py")],
        input=json.dumps(item),
        text=True,
        check=True,
        cwd=str(BASE),
    )
    print(kw)
