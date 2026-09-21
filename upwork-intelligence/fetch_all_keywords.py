#!/usr/bin/env python3
"""
Fetch all keywords via Upwork MCP (stdio JSON-RPC in UPWORK_MCP_CMD).
Appends to search_results.jsonl and raw_batches/*.json, then runs .run_process.py.
"""
import hashlib
import importlib.machinery
import json
import os
import subprocess
import sys
import time
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path

BASE = Path(__file__).resolve().parent
ORG = "1472686528932380673"
OUT = BASE / "search_results.jsonl"
RAW = BASE / "raw_batches"

_loader = importlib.machinery.SourceFileLoader("proc", str(BASE / ".run_process.py"))
_spec = spec_from_loader("proc", _loader)
proc = module_from_spec(_spec)
_loader.exec_module(proc)


def slug(kw):
    return hashlib.md5(kw.encode()).hexdigest()[:12]


def has_kw(kw):
    p = RAW / f"{slug(kw)}.json"
    if not p.exists():
        return False
    d = json.loads(p.read_text())
    return not d.get("error") and d.get("response", {}).get("status") == "ok"


def mcp_search(query):
    cmd = os.environ.get("UPWORK_MCP_CMD")
    if not cmd:
        return None
    req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "upwork__find_jobs",
            "arguments": {
                "action": "search",
                "org_uid": ORG,
                "params": {"query": query, "sort": "recency", "limit": 10},
            },
        },
    }
    run = subprocess.run(
        cmd, shell=True, input=json.dumps(req), capture_output=True, text=True, timeout=120
    )
    if run.returncode != 0:
        return {"status": "error", "error_code": "RUNNER_FAILED", "detail": run.stderr[:500]}
    try:
        out = json.loads(run.stdout)
        content = out.get("result", {}).get("content", [])
        if content and content[0].get("type") == "text":
            return json.loads(content[0]["text"])
    except Exception as e:
        return {"status": "error", "error_code": "PARSE", "detail": str(e)}
    return {"status": "error", "error_code": "EMPTY"}


def persist(keyword, group, resp):
    subprocess.run(
        [sys.executable, str(BASE / "persist_kw.py"), keyword, group],
        input=json.dumps(resp),
        text=True,
        check=True,
        cwd=str(BASE),
    )


def main():
    RAW.mkdir(exist_ok=True)
    if not os.environ.get("UPWORK_MCP_CMD"):
        pending = []
        for g, kws in proc.KEYWORD_GROUPS.items():
            for kw in kws:
                if not has_kw(kw):
                    pending.append(kw)
        print(json.dumps({"pending": len(pending), "keywords": pending[:5]}))
        sys.exit(2)

    OUT.write_text("")
    (RAW / "all.jsonl").write_text("")

    failed = []
    for g, kws in proc.KEYWORD_GROUPS.items():
        for kw in kws:
            resp = mcp_search(kw)
            if not resp or resp.get("status") != "ok":
                failed.append(kw)
                resp = resp or {"status": "error", "jobs": []}
            persist(kw, g, resp)
            time.sleep(0.3)

    subprocess.run([sys.executable, str(BASE / ".run_process.py")], check=True, cwd=str(BASE))
    print(json.dumps({"failed": failed, "failed_count": len(failed)}))


if __name__ == "__main__":
    main()
