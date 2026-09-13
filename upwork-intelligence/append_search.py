#!/usr/bin/env python3
import json
import sys
from pathlib import Path

entry = json.load(sys.stdin)
path = Path(__file__).parent / "batches.jsonl"
with open(path, "a") as f:
    f.write(json.dumps(entry) + "\n")
