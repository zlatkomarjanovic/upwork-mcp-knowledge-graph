#!/usr/bin/env python3
"""Save one Upwork find_jobs response: keyword group < jobs.json"""
import json
import re
import sys
from pathlib import Path

if len(sys.argv) < 4:
    sys.exit("usage: _mcp_save.py KEYWORD GROUP JOBS_JSON_FILE")

keyword, group, jobs_path = sys.argv[1], sys.argv[2], sys.argv[3]
jobs = json.loads(Path(jobs_path).read_text())
slug = re.sub(r"[^a-z0-9]+", "-", keyword.lower()).strip("-")[:80]
out_dir = Path(__file__).resolve().parent / "raw_batches"
out_dir.mkdir(exist_ok=True)
payload = {"keyword": keyword, "group": group, "jobs": jobs}
(out_dir / f"{slug}.json").write_text(json.dumps(payload))
print(slug)
