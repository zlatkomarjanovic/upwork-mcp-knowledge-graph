#!/usr/bin/env python3
"""
Sequential Upwork find_jobs runner for automation environments with MCP stdio bridge.
Reads keywords from .run_process.KEYWORD_GROUPS, writes raw_batches/*.json.
Requires UPWORK_MCP_CMD env (optional) — if unset, exits 0 after printing pending count.
"""
import json, hashlib, os, subprocess, sys, time
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
import importlib.machinery
from importlib.util import module_from_spec, spec_from_loader

loader = importlib.machinery.SourceFileLoader("proc", str(BASE / ".run_process.py"))
spec = spec_from_loader("proc", loader)
proc = module_from_spec(spec)
loader.exec_module(proc)

ORG = "1472686528932380673"
RAW = BASE / "raw_batches"
RAW.mkdir(exist_ok=True)


def slug(kw):
    return hashlib.md5(kw.encode()).hexdigest()[:12]


def save(kw, group, resp):
    p = RAW / f"{slug(kw)}.json"
    payload = {"keyword": kw, "group": group, "response": resp}
    if resp.get("status") == "error":
        payload["error"] = True
    p.write_text(json.dumps(payload))


def mcp_find_jobs(query):
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
    proc_run = subprocess.run(
        cmd, shell=True, input=json.dumps(req), capture_output=True, text=True, timeout=120
    )
    if proc_run.returncode != 0:
        return {"status": "error", "error_code": "RUNNER_FAILED", "detail": proc_run.stderr[:500]}
    try:
        out = json.loads(proc_run.stdout)
        content = out.get("result", {}).get("content", [])
        if content and content[0].get("type") == "text":
            return json.loads(content[0]["text"])
    except Exception as e:
        return {"status": "error", "error_code": "PARSE", "detail": str(e)}
    return {"status": "error", "error_code": "EMPTY"}


def main():
    pending = []
    for g, kws in proc.KEYWORD_GROUPS.items():
        for kw in kws:
            p = RAW / f"{slug(kw)}.json"
            if p.exists():
                d = json.loads(p.read_text())
                if not d.get("error") and d.get("response", {}).get("status") == "ok":
                    continue
            pending.append((kw, g))

    if not os.environ.get("UPWORK_MCP_CMD"):
        print(json.dumps({"pending": len(pending), "note": "Set UPWORK_MCP_CMD for autonomous fetch"}))
        return

    errors = []
    for i, (kw, g) in enumerate(pending):
        resp = mcp_find_jobs(kw)
        if resp is None:
            break
        save(kw, g, resp)
        if resp.get("status") == "error":
            errors.append(kw)
            if resp.get("error_code") == "SENSITIVE_RATE_LIMIT_EXCEEDED":
                time.sleep(max(5, int(resp.get("retry_after_seconds", 5))))
                resp2 = mcp_find_jobs(kw)
                if resp2:
                    save(kw, g, resp2)
                    if resp2.get("status") != "error":
                        errors.pop()
        if (i + 1) % 10 == 0:
            time.sleep(6)
    print(json.dumps({"completed": len(pending) - len(errors), "errors": errors}))


if __name__ == "__main__":
    main()
