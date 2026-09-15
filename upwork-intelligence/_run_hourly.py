#!/usr/bin/env python3
"""Merge search queue into raw run and execute processor."""
import json
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
QUEUE = BASE / "_search_queue.jsonl"
RAW = BASE / "_raw_run.json"
PROCESS = BASE / "_process_run.py"


def merge_queue():
    if not QUEUE.exists():
        return 0
    raw = json.loads(RAW.read_text())
    done = {s["keyword"] for s in raw["searches"]}
    added = 0
    with QUEUE.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            kw = entry.get("keyword")
            if not kw or kw in done:
                continue
            raw["searches"].append(entry)
            done.add(kw)
            added += 1
    raw["meta"]["keywordsCompleted"] = len(raw["searches"])
    RAW.write_text(json.dumps(raw))
    if added:
        QUEUE.write_text("")
    return added


def main():
    added = merge_queue()
    print(json.dumps({"merged": added, "searches": len(json.loads(RAW.read_text())["searches"])}))
    subprocess.check_call([sys.executable, str(PROCESS)])


if __name__ == "__main__":
    main()
