#!/usr/bin/env python3
import json, sys
from pathlib import Path
p = Path(__file__).parent / "search_responses.jsonl"
for line in sys.stdin:
    line = line.strip()
    if line:
        with p.open("a") as f:
            f.write(line + "\n")
