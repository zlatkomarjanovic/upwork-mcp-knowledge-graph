#!/usr/bin/env python3
"""Import [{keyword, group, jobs}, ...] into raw_batches/."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BATCH_DIR = ROOT / "raw_batches"
BATCH_DIR.mkdir(exist_ok=True)

data = json.loads(Path(sys.argv[1]).read_text())
for item in data:
    kw = item["keyword"]
    grp = item["group"]
    jobs = item.get("jobs") or []
    slug = re.sub(r"[^a-z0-9]+", "-", kw.lower()).strip("-")[:80]
    (BATCH_DIR / f"{slug}.json").write_text(json.dumps({"keyword": kw, "group": grp, "jobs": jobs}))
print(len(data))
