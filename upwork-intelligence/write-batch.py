#!/usr/bin/env python3
"""Write one raw_batches entry from jobs JSON file."""
import json
import re
import sys
from pathlib import Path

if len(sys.argv) != 4:
    sys.exit("usage: write-batch.py KEYWORD GROUP JOBS.json")

keyword, group, jobs_path = sys.argv[1], sys.argv[2], sys.argv[3]
jobs = json.loads(Path(jobs_path).read_text())
if isinstance(jobs, dict) and "jobs" in jobs:
    jobs = jobs["jobs"]
slug = re.sub(r"[^a-z0-9]+", "-", keyword.lower()).strip("-")[:80]
out_dir = Path(__file__).resolve().parent / "raw_batches"
out_dir.mkdir(exist_ok=True)
(out_dir / f"{slug}.json").write_text(
    json.dumps({"keyword": keyword, "group": group, "jobs": jobs})
)
print(slug)
