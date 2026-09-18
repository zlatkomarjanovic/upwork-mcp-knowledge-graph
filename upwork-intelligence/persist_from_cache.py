#!/usr/bin/env python3
"""Write all mcp_cache.json entries to raw_batches and search_results.jsonl."""
import hashlib
import importlib.machinery
import json
import sys
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path

BASE = Path(__file__).resolve().parent
CACHE = BASE / "mcp_cache.json"
RAW = BASE / "raw_batches"

_loader = importlib.machinery.SourceFileLoader("proc", str(BASE / ".run_process.py"))
_spec = spec_from_loader("proc", _loader)
proc = module_from_spec(_spec)
_loader.exec_module(proc)

kw_to_group = {}
for g, kws in proc.KEYWORD_GROUPS.items():
    for kw in kws:
        kw_to_group[kw] = g


def slug(kw):
    return hashlib.md5(kw.encode()).hexdigest()[:12]


def main():
    if not CACHE.exists():
        print(json.dumps({"error": "no cache"}))
        sys.exit(1)
    cache = json.loads(CACHE.read_text())
    RAW.mkdir(exist_ok=True)
    from save_mcp_compact import save_item  # noqa: E402

    n = 0
    for kw, resp in cache.items():
        group = kw_to_group.get(kw, "UNKNOWN")
        err = resp.get("status") != "ok"
        save_item(kw, group, resp, err)
        n += 1
    print(json.dumps({"persisted": n}))


if __name__ == "__main__":
    main()
