#!/usr/bin/env python3
"""Append MCP search entries to search_responses.json (stdin: JSON array)."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
path = ROOT / "search_responses.json"
data = json.loads(path.read_text()) if path.exists() else []
data.extend(json.load(sys.stdin))
path.write_text(json.dumps(data, ensure_ascii=False))
