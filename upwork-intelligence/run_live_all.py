#!/usr/bin/env python3
"""Fetch all keywords via _mcp_call.py and refresh search_responses.json."""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent
KEYWORDS = list(json.loads((ROOT / "keywords.json").read_text())["keywords"].keys())
ORG = json.loads((ROOT / "keywords.json").read_text())["org_uid"]
SEARCH = ROOT / "search_responses.json"
GROUPS = json.loads((ROOT / "keywords.json").read_text())["keywords"]
MCP = ROOT / "_mcp_call.py"


def find_jobs(keyword: str) -> dict:
    payload = {
        "namespace": "Upwork",
        "toolName": "upwork__find_jobs",
        "arguments": {
            "action": "search",
            "org_uid": ORG,
            "params": {"query": keyword, "sort": "recency", "limit": 10},
        },
    }
    out = subprocess.check_output([sys.executable, str(MCP), json.dumps(payload)], text=True)
    return json.loads(out)


def main() -> int:
    paired = []
    errors: list[str] = []
    for i, kw in enumerate(KEYWORDS):
        for attempt in range(4):
            try:
                resp = find_jobs(kw)
            except subprocess.CalledProcessError as e:
                resp = {"status": "error", "error_code": "SUBPROCESS", "reason": str(e)[:200]}
            if resp.get("error_code") == "SENSITIVE_RATE_LIMIT_EXCEEDED":
                wait = int(resp.get("retry_after_seconds") or 6) + 1
                time.sleep(wait)
                continue
            break
        group = GROUPS.get(kw, "OTHER")
        if resp.get("status") == "error" and not resp.get("jobs"):
            errors.append(kw)
            paired.append({"keyword": kw, "group": group, "response": resp})
        else:
            paired.append({"keyword": kw, "group": group, "response": resp})
        if (i + 1) % 10 == 0:
            print(f"{i + 1}/{len(KEYWORDS)}", flush=True)
    SEARCH.write_text(json.dumps(paired, indent=2))
    print(json.dumps({"completed": len(KEYWORDS) - len(errors), "errors": len(errors), "failed": errors[:20]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
