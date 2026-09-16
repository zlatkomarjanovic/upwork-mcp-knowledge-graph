#!/usr/bin/env python3
"""Merge a batch of {keyword, response} into search_responses.json."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent
SEARCH = ROOT / "search_responses.json"
GROUPS = json.loads((ROOT / "keywords.json").read_text())["keywords"]


def slim(resp: dict) -> dict:
    jobs = []
    for j in resp.get("jobs") or []:
        jobs.append({k: v for k, v in j.items() if k != "description_snippet"})
    out: dict = {"status": resp.get("status", "ok"), "jobs": jobs}
    for k in ("error_code", "reason", "status"):
        if k in resp and k != "status":
            out[k] = resp[k]
    if resp.get("status") == "error":
        out["status"] = "error"
    return out


def main() -> None:
    batch = json.loads(sys.stdin.read())
    paired = json.loads(SEARCH.read_text()) if SEARCH.exists() else []
    index = {e["keyword"]: i for i, e in enumerate(paired)}
    applied = 0
    for item in batch:
        kw = item["keyword"]
        if kw not in GROUPS:
            continue
        entry = {"keyword": kw, "group": GROUPS[kw], "response": slim(item["response"])}
        if kw in index:
            paired[index[kw]] = entry
        else:
            paired.append(entry)
        applied += 1
    SEARCH.write_text(json.dumps(paired, indent=2))
    print(json.dumps({"applied": applied, "total_entries": len(paired)}))


if __name__ == "__main__":
    main()
