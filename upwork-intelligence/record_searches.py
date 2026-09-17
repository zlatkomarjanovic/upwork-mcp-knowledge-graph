#!/usr/bin/env python3
"""Merge MCP search batch from stdin into search_responses.json."""
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
    out = {"status": resp.get("status", "ok"), "jobs": jobs}
    for k in ("hasMore", "next_cursor", "pageInfo", "error", "error_code"):
        if k in resp:
            out[k] = resp[k]
    return out


def main():
    batch = json.loads(sys.stdin.read())
    paired = json.loads(SEARCH.read_text()) if SEARCH.exists() else []
    index = {e["keyword"]: i for i, e in enumerate(paired)}
    for item in batch:
        kw = item["keyword"]
        resp = item.get("response") or item.get("mcp") or {}
        entry = {
            "keyword": kw,
            "group": GROUPS.get(kw, item.get("group", "OTHER")),
            "response": slim(resp),
        }
        if kw in index:
            paired[index[kw]] = entry
        else:
            paired.append(entry)
            index[kw] = len(paired) - 1
    SEARCH.write_text(json.dumps(paired, indent=2))
    print(len(paired))


if __name__ == "__main__":
    main()
