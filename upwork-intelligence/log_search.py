#!/usr/bin/env python3
"""Append one search to search_log.jsonl. Args: KEYWORD path/to/result.json"""
import json
import sys
from pathlib import Path

kw = sys.argv[1]
result = json.loads(Path(sys.argv[2]).read_text())
line = json.dumps({"kw": kw, "result": result}, separators=(",", ":"))
Path(__file__).parent.joinpath("search_log.jsonl").open("a").write(line + "\n")
