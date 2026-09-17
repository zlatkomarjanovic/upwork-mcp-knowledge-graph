#!/usr/bin/env python3
"""
Append Upwork find_jobs results to run_data.jsonl.

Designed for automation: invoke from agent after each MCP batch, passing
JSON on stdin shaped as {"items":[{"keyword":"...","mcp":{...}}]}.
"""
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
OUT = BASE / "run_data.jsonl"


def main():
    data = json.loads(sys.stdin.read())
    with OUT.open("a") as f:
        for item in data.get("items") or []:
            f.write(
                json.dumps(
                    {"keyword": item["keyword"], "mcp": item["mcp"]},
                    ensure_ascii=False,
                )
                + "\n"
            )
    print("appended", len(data.get("items") or []))


if __name__ == "__main__":
    main()
