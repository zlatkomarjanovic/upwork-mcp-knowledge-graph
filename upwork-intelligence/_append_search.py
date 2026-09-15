#!/usr/bin/env python3
"""Append one search result object to search-results-raw.json."""
import json, sys
from pathlib import Path

path = Path(__file__).parent / "search-results-raw.json"
data = json.loads(path.read_text())
data["searches"].append(json.loads(sys.argv[1]))
path.write_text(json.dumps(data))
