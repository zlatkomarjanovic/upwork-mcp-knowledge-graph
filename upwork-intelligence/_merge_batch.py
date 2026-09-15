#!/usr/bin/env python3
"""Append search batch entries to search-results-raw.json from stdin JSON lines."""
import json, sys
from pathlib import Path

path = Path(__file__).parent / "search-results-raw.json"
data = json.loads(path.read_text())
for line in sys.stdin:
    line = line.strip()
    if line:
        data["searches"].append(json.loads(line))
path.write_text(json.dumps(data))
