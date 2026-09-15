#!/usr/bin/env bash
# Agent-driven: prints keywords still missing mcp_raw/*.json
set -euo pipefail
cd "$(dirname "$0")"
python3 fetch_all_keywords.py || true
python3 - <<'PY'
import json, re
from pathlib import Path
BASE = Path(".")
keywords = [ln.strip() for ln in (BASE/"keywords.txt").read_text().splitlines() if ln.strip()]
out = BASE/"mcp_raw"
def slug(k): return re.sub(r"[^a-z0-9]+", "_", k.lower()).strip("_")
missing = [k for k in keywords if not (out/f"{slug(k)}.json").exists()]
print(len(missing))
PY
