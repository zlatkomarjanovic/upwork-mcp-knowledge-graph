#!/usr/bin/env python3
"""Write per-keyword raw batch JSON from a chunk file (array of {keyword, group, response})."""
import hashlib
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent / "raw_batches"
BASE.mkdir(exist_ok=True)
chunk = json.loads(Path(sys.argv[1]).read_text())
for item in chunk:
    kw = item["keyword"]
    slug = hashlib.md5(kw.encode()).hexdigest()[:12]
    (BASE / f"{slug}.json").write_text(json.dumps(item, ensure_ascii=False))
print(len(chunk))
