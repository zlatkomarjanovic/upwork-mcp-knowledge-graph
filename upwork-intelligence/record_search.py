#!/usr/bin/env python3
"""Record one keyword search into batches.jsonl."""
import json
import sys
from pathlib import Path

BASE = Path(__file__).parent
path = BASE / "batches.jsonl"
entry = {
    "keyword": sys.argv[1],
    "group": sys.argv[2],
    "jobs": json.loads(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3] != "ERROR" else [],
    "error": len(sys.argv) > 3 and sys.argv[3] == "ERROR",
}
with open(path, "a") as f:
    f.write(json.dumps(entry) + "\n")
