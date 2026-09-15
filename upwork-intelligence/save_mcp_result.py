#!/usr/bin/env python3
"""Save one MCP response file: save_mcp_result.py KEYWORD path/to/response.json"""
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
from run_all_keywords import append_batch, strip_job  # noqa: E402

kw = sys.argv[1]
raw = json.loads(Path(sys.argv[2]).read_text())
if raw.get("status") == "error" or raw.get("error_code"):
    append_batch(kw, [], error=True)
else:
    jobs = [strip_job(j) for j in raw.get("jobs", [])]
    append_batch(kw, jobs)
