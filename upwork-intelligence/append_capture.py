#!/usr/bin/env python3
"""Append one capture line: append_capture.py KEYWORD RESPONSE_JSON_FILE"""
import json
import sys
from pathlib import Path

CAP = Path(__file__).resolve().parent / "capture.jsonl"


def main():
    kw, src = sys.argv[1], Path(sys.argv[2])
    resp = json.loads(src.read_text())
    with CAP.open("a") as f:
        f.write(json.dumps({"keyword": kw, "response": resp}, ensure_ascii=False) + "\n")
    print("captured", kw)


if __name__ == "__main__":
    main()
