#!/usr/bin/env python3
import json, sys
from pathlib import Path
p = Path(__file__).parent / "run-results.jsonl"
row = {"keyword": sys.argv[1], "response": json.load(sys.stdin)}
if len(sys.argv) > 2 and sys.argv[2] == "error":
    row = {"keyword": sys.argv[1], "error": sys.argv[3]}
with p.open("a") as f:
    f.write(json.dumps(row, ensure_ascii=False) + "\n")
