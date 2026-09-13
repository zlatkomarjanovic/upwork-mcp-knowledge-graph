#!/usr/bin/env python3
"""Append one search entry to search_responses.json."""
import json
import sys
from pathlib import Path

BASE = Path(__file__).parent
path = BASE / "search_responses.json"
if path.exists():
    data = json.loads(path.read_text())
else:
    data = {"searches": [], "errors": []}

entry = json.loads(sys.argv[1])
data["searches"].append(entry)
path.write_text(json.dumps(data))
