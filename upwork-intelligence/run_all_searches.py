#!/usr/bin/env python3
"""
Fetch all keyword searches via Upwork MCP and append to search_results.jsonl.

Requires UPWORK_MCP_CMD (stdio JSON-RPC to upwork__find_jobs), same as hourly_mcp_runner.
When unset, prints pending keywords and exits 2 so the cloud agent can MCP-fetch manually.
"""
import hashlib
import importlib.machinery
import json
import os
import subprocess
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent
from importlib.util import module_from_spec, spec_from_loader

_loader = importlib.machinery.SourceFileLoader("proc", str(BASE / ".run_process.py"))
_spec = spec_from_loader("proc", _loader)
proc = module_from_spec(_spec)
_loader.exec_module(proc)
ORG = "1472686528932380673"
OUT = BASE / "search_results.jsonl"
RAW = BASE / "raw_batches"
RAW.mkdir(exist_ok=True)


def slug(kw):
    return hashlib.md5(kw.encode()).hexdigest()[:12]


def already_done(kw):
    if OUT.exists():
        for line in OUT.read_text().splitlines():
            if line.strip():
                d = json.loads(line)
                if d.get("keyword") == kw:
                    return True
    p = RAW / f"{slug(kw)}.json"
    return p.exists()


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


def save_line(keyword, group, resp):
    payload = {"keyword": keyword, "group": group, "response": resp}
    if resp.get("status") != "ok":
        payload["error"] = True
    with OUT.open("a") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    (RAW / f"{slug(keyword)}.json").write_text(json.dumps(payload, ensure_ascii=False))


def main():
    pending = []
    for g, kws in proc.KEYWORD_GROUPS.items():
        for kw in kws:
            if not already_done(kw):
                pending.append((kw, g))
    if not pending:
        print(json.dumps({"ok": True, "pending": 0}))
        return
    if not os.environ.get("UPWORK_MCP_CMD"):
        print(json.dumps({"pending": len(pending), "keywords": [p[0] for p in pending[:20]]}))
        sys.exit(2)
    errors = []
    for i, (kw, g) in enumerate(pending):
        resp = mcp_search(kw)
        if resp is None:
            errors.append(kw)
            continue
        save_line(kw, g, resp)
        if (i + 1) % 6 == 0:
            time.sleep(5)
    print(json.dumps({"ok": True, "saved": len(pending) - len(errors), "errors": errors}))


if __name__ == "__main__":
    main()
