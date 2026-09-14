#!/usr/bin/env python3
"""Print keyword slice for MCP wave (start count)."""
import json
import sys
from pathlib import Path

kws = json.loads((Path(__file__).parent / "keywords.json").read_text())
start = int(sys.argv[1])
count = int(sys.argv[2])
for k in kws[start : start + count]:
    print(json.dumps(k, ensure_ascii=False))
