#!/usr/bin/env python3
"""Ingest slim MCP JSON files from _resp/ into _search_queue.jsonl."""
import json
import sys
from pathlib import Path

from _add_searches import slim

BASE = Path(__file__).resolve().parent
RESP = BASE / "_resp"
QUEUE = BASE / "_search_queue.jsonl"


def main():
    paths = sorted(RESP.glob("*.json"))
    if not paths:
        print("no files", file=sys.stderr)
        return 1
    with QUEUE.open("a") as out:
        for p in paths:
            data = json.loads(p.read_text())
            kw = data.get("keyword") or p.stem.split("_", 1)[-1].replace("_", " ")
            resp = data.get("response") or data
            out.write(
                json.dumps({"keyword": kw, "response": slim(resp)}, separators=(",", ":"))
                + "\n"
            )
            p.unlink()
    print(len(paths))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
