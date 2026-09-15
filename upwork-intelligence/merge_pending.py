#!/usr/bin/env python3
"""Append one or more saved responses to pending.json.

Usage:
  merge_pending.py KEYWORD RESPONSE_JSON_FILE
  merge_pending.py --batch BATCH_JSON_FILE   # [{keyword, response}, ...]
"""
import json
import sys
from pathlib import Path

PENDING = Path(__file__).resolve().parent / "pending.json"


def load():
    if PENDING.exists():
        return json.loads(PENDING.read_text())
    return {"responses": []}


def save(data):
    PENDING.write_text(json.dumps(data, ensure_ascii=False))


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "--batch":
        batch = json.loads(Path(sys.argv[2]).read_text())
        data = load()
        data["responses"].extend(batch)
        save(data)
        print("pending", len(data["responses"]))
        return
    kw, src = sys.argv[1], Path(sys.argv[2])
    resp = json.loads(src.read_text())
    data = load()
    data["responses"].append({"keyword": kw, "response": resp})
    save(data)
    print("pending", len(data["responses"]))


if __name__ == "__main__":
    main()
