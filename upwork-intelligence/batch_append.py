#!/usr/bin/env python3
import json
import sys
from pathlib import Path

path = Path(__file__).parent / ".run-searches.jsonl"
records = json.load(sys.stdin)
with path.open("a") as f:
    for rec in records:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
