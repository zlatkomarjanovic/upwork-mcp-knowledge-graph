#!/usr/bin/env python3
"""Append batch file [{keyword, response}, ...] to capture.jsonl"""
import json
import sys
from pathlib import Path

CAP = Path(__file__).resolve().parent / "capture.jsonl"


def main():
    batch = json.loads(Path(sys.argv[1]).read_text())
    with CAP.open("a") as f:
        for item in batch:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print("appended", len(batch))


if __name__ == "__main__":
    main()
