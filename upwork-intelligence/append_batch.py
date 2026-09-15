#!/usr/bin/env python3
import json, sys
from pathlib import Path
p = Path(__file__).parent / "_search_batches.jsonl"
for arg in sys.argv[1:]:
    p.write_text(p.read_text() + arg + "\n" if p.exists() else arg + "\n")
# also accept stdin
if not sys.stdin.isatty():
    with p.open("a") as f:
        f.write(sys.stdin.read())
