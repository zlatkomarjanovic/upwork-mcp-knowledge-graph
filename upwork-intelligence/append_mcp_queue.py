#!/usr/bin/env python3
"""Append one or more keyword search lines to mcp-queue.jsonl."""
import json
import sys
from pathlib import Path

QUEUE = Path(__file__).parent / "mcp-queue.jsonl"


def main() -> None:
    payload = json.loads(sys.stdin.read())
    items = payload if isinstance(payload, list) else [payload]
    with QUEUE.open("a") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(len(items))


if __name__ == "__main__":
    main()
