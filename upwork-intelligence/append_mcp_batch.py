#!/usr/bin/env python3
"""Append MCP find_jobs results keyed by keyword into search_responses.json."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent
SEARCH = ROOT / "search_responses.json"
GROUPS = json.loads((ROOT / "keywords.json").read_text())["keywords"]


def slim(resp: dict) -> dict:
    jobs = []
    for j in resp.get("jobs") or []:
        jobs.append({k: j[k] for k in j if k != "description_snippet"})
    out = {k: resp[k] for k in resp if k != "jobs"}
    out["jobs"] = jobs
    return out


def main():
    batch = json.loads(Path(sys.argv[1]).read_text())
    paired = json.loads(SEARCH.read_text())
    index = {e["keyword"]: i for i, e in enumerate(paired)}
    for item in batch:
        kw = item["keyword"]
        resp = slim(item["response"])
        entry = {"keyword": kw, "group": GROUPS.get(kw, "OTHER"), "response": resp}
        if kw in index:
            paired[index[kw]] = entry
        else:
            paired.append(entry)
    SEARCH.write_text(json.dumps(paired, indent=2))
    ok = sum(1 for e in paired if e["response"].get("status") == "ok")
    pending = sum(1 for e in paired if e["response"].get("error_code") == "PENDING")
    print(f"ok={ok} pending={pending} total={len(paired)}")


if __name__ == "__main__":
    main()
