#!/usr/bin/env python3
"""Run all keyword searches sequentially via _mcp_call.py; update search_responses.json."""
import json
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).parent
KW = json.loads((ROOT / "keywords.json").read_text())
ORG = KW["org_uid"]
KEYWORDS = list(KW["keywords"].keys())
SEARCH = ROOT / "search_responses.json"
MCP = ROOT / "_mcp_call.py"
DELAY = 5.2


def slim(resp: dict) -> dict:
    jobs = []
    for j in resp.get("jobs") or []:
        jobs.append({k: j[k] for k in j if k != "description_snippet"})
    out = {k: resp[k] for k in resp if k not in ("jobs", "client_rating_basis")}
    out["jobs"] = jobs
    if resp.get("status") != "ok" and not jobs:
        out.setdefault("status", resp.get("status", "error"))
    return out


def mcp_search(keyword: str) -> dict:
    payload = {
        "action": "search",
        "org_uid": ORG,
        "params": {"query": keyword, "sort": "recency", "limit": 10},
    }
    try:
        out = subprocess.check_output(
            ["python3", str(MCP), json.dumps(payload)],
            text=True,
            timeout=120,
        )
        return json.loads(out)
    except Exception as e:
        return {"status": "error", "error": str(e)}


def main() -> None:
    paired = []
    errors = []
    for i, keyword in enumerate(KEYWORDS):
        resp = mcp_search(keyword)
        if resp.get("status") == "error" or resp.get("error_code"):
            errors.append(keyword)
        group = KW["keywords"][keyword]
        paired.append({"keyword": keyword, "group": group, "response": slim(resp)})
        if (i + 1) % 10 == 0:
            print(f"progress {i+1}/{len(KEYWORDS)} errors={len(errors)}", flush=True)
        if i + 1 < len(KEYWORDS):
            time.sleep(DELAY)
    SEARCH.write_text(json.dumps(paired, indent=2))
    print(json.dumps({"keywords": len(paired), "errors": errors, "error_count": len(errors)}))


if __name__ == "__main__":
    main()
