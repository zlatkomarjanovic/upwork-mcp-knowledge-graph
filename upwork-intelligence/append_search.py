#!/usr/bin/env python3
"""Append one search result entry to search_responses.json."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
path = ROOT / "search_responses.json"
data = json.loads(path.read_text()) if path.exists() else []
data.append(json.loads(sys.stdin.read()))
path.write_text(json.dumps(data, ensure_ascii=False))
