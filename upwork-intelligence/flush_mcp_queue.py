#!/usr/bin/env python3
"""Write mcp_queue/*.json into raw_batches and search_results.jsonl via persist_kw."""
import hashlib
import importlib.machinery
import json
import subprocess
import sys
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path

BASE = Path(__file__).resolve().parent
QUEUE = BASE / "mcp_queue"

_loader = importlib.machinery.SourceFileLoader("proc", str(BASE / ".run_process.py"))
_spec = spec_from_loader("proc", _loader)
proc = module_from_spec(_spec)
_loader.exec_module(proc)


def slug(kw):
    return hashlib.md5(kw.encode()).hexdigest()[:12]


def main():
    kw_to_group = {}
    for g, kws in proc.KEYWORD_GROUPS.items():
        for kw in kws:
            kw_to_group[kw] = g

    done = 0
    for kw, group in kw_to_group.items():
        p = QUEUE / f"{slug(kw)}.json"
        if not p.exists():
            continue
        data = json.loads(p.read_text())
        resp = data.get("response") or data
        subprocess.run(
            [sys.executable, str(BASE / "persist_kw.py"), kw, group],
            input=json.dumps(resp),
            text=True,
            check=True,
            cwd=str(BASE),
        )
        done += 1
    print("flushed", done)


if __name__ == "__main__":
    main()
