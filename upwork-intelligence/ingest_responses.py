#!/usr/bin/env python3
"""Ingest mcp_raw/*.json (full MCP response + keyword field) into _search_batches.jsonl"""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
RAW = BASE / "mcp_raw"
sys_path = BASE / "run_all_keywords.py"
import importlib.util

spec = importlib.util.spec_from_file_location("rak", BASE / "run_all_keywords.py")
rak = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rak)

RAW.mkdir(exist_ok=True)
for path in sorted(RAW.glob("*.json")):
    data = json.loads(path.read_text())
    kw = data["keyword"]
    resp = data.get("response", data)
    if resp.get("status") == "error":
        rak.append_batch(kw, [], error=True)
    else:
        jobs = [rak.strip_job(j) for j in resp.get("jobs", [])]
        rak.append_batch(kw, jobs)

print("ingested", len(list(RAW.glob("*.json"))), "files")
