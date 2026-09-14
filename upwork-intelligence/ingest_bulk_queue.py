#!/usr/bin/env python3
"""Ingest mcp_queue/_bulk.json array of {keyword, group?, response} into mcp_queue/*.json"""
import hashlib
import importlib.machinery
import json
import sys
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path

BASE = Path(__file__).resolve().parent
QUEUE = BASE / "mcp_queue"
QUEUE.mkdir(exist_ok=True)

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
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else BASE / "mcp_queue" / "_bulk.json"
    items = json.loads(path.read_text())
    if isinstance(items, dict):
        items = items.get("items", [])
    n = 0
    for item in items:
        kw = item["keyword"]
        group = item.get("group") or kw_to_group.get(kw, "UNKNOWN")
        payload = {"keyword": kw, "group": group, "response": item["response"]}
        (QUEUE / f"{slug(kw)}.json").write_text(json.dumps(payload, ensure_ascii=False))
        n += 1
    print(n)


if __name__ == "__main__":
    main()
