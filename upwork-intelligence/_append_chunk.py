#!/usr/bin/env python3
"""Append one search chunk: keyword, group, jobs (or error) to search-results-raw.json."""
import json
import sys
from pathlib import Path

path = Path(__file__).parent / "search-results-raw.json"
data = json.loads(path.read_text())
chunk = json.loads(sys.argv[1])
data["searches"].append(chunk)
if chunk.get("error"):
    data.setdefault("errors", []).append(chunk["keyword"])
path.write_text(json.dumps(data))
