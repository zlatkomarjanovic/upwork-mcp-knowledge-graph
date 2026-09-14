#!/usr/bin/env python3
import json
import sys
from pathlib import Path

path = Path(__file__).parent / ".run-searches.jsonl"
line = sys.stdin.read().strip()
if line:
    with path.open("a") as f:
        f.write(line + "\n")
