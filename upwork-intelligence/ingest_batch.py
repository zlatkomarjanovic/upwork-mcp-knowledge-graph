#!/usr/bin/env python3
"""Ingest {"items":[{"keyword","mcp":{...}}]} into mcp_raw/."""
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
from save_mcp_raw import slug, slim_job  # type: ignore

RAW = BASE / "mcp_raw"
RAW.mkdir(exist_ok=True)

data = json.loads(Path(sys.argv[1]).read_text())
for item in data["items"]:
    kw = item["keyword"]
    raw = item["mcp"]
    out = {
        "status": raw.get("status", "ok"),
        "jobs": [slim_job(j) for j in (raw.get("jobs") or [])],
    }
    if raw.get("error"):
        out["error"] = raw["error"]
    (RAW / f"{slug(kw)}.json").write_text(json.dumps(out, ensure_ascii=False))
print("ingested", len(data["items"]))
