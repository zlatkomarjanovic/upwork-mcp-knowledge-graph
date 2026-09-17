#!/usr/bin/env python3
"""Fetch all keywords via Cursor dynamic Upwork MCP (cloud agent only).

Writes slim responses to search_responses.json after each keyword.
Requires running inside an environment where `cursor` MCP bridge works.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
KW_FILE = ROOT / "keywords.json"
SEARCH = ROOT / "search_responses.json"
META = json.loads(KW_FILE.read_text())
KEYWORDS = list(META["keywords"].keys())
ORG = META["org_uid"]


def slim(resp: dict) -> dict:
    jobs = [{k: v for k, v in j.items() if k != "description_snippet"} for j in (resp.get("jobs") or [])]
    out = {"status": resp.get("status", "ok"), "jobs": jobs}
    for k in ("hasMore", "next_cursor", "pageInfo", "error", "error_code"):
        if k in resp:
            out[k] = resp[k]
    return out


def mcp_find_jobs(keyword: str) -> dict:
    raise RuntimeError(
        "MCP CLI unavailable in this environment; use agent CallDynamicTool + record_searches.py"
    )


def load_paired():
    if SEARCH.exists():
        return json.loads(SEARCH.read_text())
    return []


def save_paired(paired: list):
    SEARCH.write_text(json.dumps(paired, indent=2))


def main():
    paired = load_paired()
    index = {e["keyword"]: i for i, e in enumerate(paired)}
    groups = META["keywords"]
    errors = []
    for i, kw in enumerate(KEYWORDS, 1):
        resp = mcp_find_jobs(kw)
        if resp.get("status") not in ("ok", None) and not resp.get("jobs"):
            errors.append(kw)
        entry = {"keyword": kw, "group": groups[kw], "response": slim(resp)}
        if kw in index:
            paired[index[kw]] = entry
        else:
            paired.append(entry)
            index[kw] = len(paired) - 1
        if i % 10 == 0:
            save_paired(paired)
            print(f"saved {i}/{len(KEYWORDS)}", flush=True)
    save_paired(paired)
    print(json.dumps({"keywords": len(KEYWORDS), "errors": errors, "entries": len(paired)}))


if __name__ == "__main__":
    main()
