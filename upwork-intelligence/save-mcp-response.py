#!/usr/bin/env python3
"""Save Upwork find_jobs MCP JSON to raw_batches/{slug}.json"""
import json
import re
import sys
from pathlib import Path

if len(sys.argv) != 4:
    sys.exit("usage: save-mcp-response.py KEYWORD GROUP MCP_JSON_FILE")

keyword, group, path = sys.argv[1], sys.argv[2], sys.argv[3]
data = json.loads(Path(path).read_text())
jobs = data.get("jobs", []) if isinstance(data, dict) else data
slug = re.sub(r"[^a-z0-9]+", "-", keyword.lower()).strip("-")[:80]
out = Path(__file__).resolve().parent / "raw_batches" / f"{slug}.json"
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps({"keyword": keyword, "group": group, "jobs": jobs}))
print(slug, len(jobs))
