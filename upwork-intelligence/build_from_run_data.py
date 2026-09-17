#!/usr/bin/env python3
"""Populate mcp_raw/ from run_data.jsonl lines: {"keyword","mcp":{...}}."""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
RAW = BASE / "mcp_raw"
RAW.mkdir(exist_ok=True)

from save_mcp_raw import slug, slim_job  # noqa: E402

path = BASE / "run_data.jsonl"
if not path.exists():
    raise SystemExit("run_data.jsonl missing")

n = 0
for line in path.read_text().splitlines():
    if not line.strip():
        continue
    rec = json.loads(line)
    kw = rec["keyword"]
    raw = rec.get("mcp") or {}
    out = {
        "status": raw.get("status", "ok"),
        "jobs": [slim_job(j) for j in (raw.get("jobs") or [])],
    }
    if raw.get("error_code") or raw.get("error"):
        out["error"] = raw.get("error_code") or raw.get("error")
    (RAW / f"{slug(kw)}.json").write_text(json.dumps(out, ensure_ascii=False))
    n += 1
print("saved", n, "keywords")
