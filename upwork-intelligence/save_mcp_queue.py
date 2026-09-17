#!/usr/bin/env python3
"""Save one MCP response: echo '{"keyword":"...","response":{...}}' | save_mcp_queue.py"""
import hashlib
import json
import sys
from pathlib import Path

QUEUE = Path(__file__).resolve().parent / "mcp_queue"
QUEUE.mkdir(exist_ok=True)


def main():
    data = json.load(sys.stdin)
    kw = data["keyword"]
    slug = hashlib.md5(kw.encode()).hexdigest()[:12]
    (QUEUE / f"{slug}.json").write_text(json.dumps(data, ensure_ascii=False))
    print(slug)


if __name__ == "__main__":
    main()
