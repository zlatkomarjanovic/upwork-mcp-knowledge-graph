#!/usr/bin/env python3
import json
import sys
from pathlib import Path

kw = sys.argv[1]
raw = json.load(sys.stdin)
jobs = raw.get("jobs", []) if raw.get("status") == "ok" else []
err = raw.get("status") != "ok"
BASE = Path(__file__).resolve().parent
CACHE = BASE / "mcp_cache"
BATCH = BASE / "_search_batches.jsonl"
CACHE.mkdir(exist_ok=True)
safe = str(abs(hash(kw)))
(CACHE / f"{safe}.json").write_text(json.dumps({"keyword": kw, "jobs": jobs}, ensure_ascii=False))
with BATCH.open("a") as f:
    f.write(json.dumps({"keyword": kw, "jobs": jobs, "error": err or None}, ensure_ascii=False) + "\n")
