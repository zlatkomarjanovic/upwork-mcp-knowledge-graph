#!/usr/bin/env python3
"""Merge live_mcp.jsonl batches into search_responses.json."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent
SEARCH = ROOT / "search_responses.json"
LIVE = ROOT / "live_mcp.jsonl"
GROUPS = json.loads((ROOT / "keywords.json").read_text())["keywords"]


def slim(resp: dict) -> dict:
    out = {k: v for k, v in resp.items() if k not in ("client_rating_basis", "description_snippet")}
    jobs = []
    for j in out.get("jobs") or []:
        jobs.append({k: v for k, v in j.items() if k != "description_snippet"})
    out["jobs"] = jobs
    return out


def main() -> None:
    if not LIVE.exists():
        print("no live_mcp.jsonl", file=sys.stderr)
        return
    paired = json.loads(SEARCH.read_text()) if SEARCH.exists() else []
    index = {e["keyword"]: i for i, e in enumerate(paired)}
    merged = 0
    for line in LIVE.read_text().splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        kw = item["keyword"]
        resp = slim(item.get("response") or {})
        entry = {"keyword": kw, "group": GROUPS.get(kw, "OTHER"), "response": resp}
        if kw in index:
            paired[index[kw]] = entry
        else:
            paired.append(entry)
            index[kw] = len(paired) - 1
        merged += 1
    SEARCH.write_text(json.dumps(paired, indent=2))
    print(json.dumps({"merged": merged, "total_keywords": len(paired)}))


if __name__ == "__main__":
    main()
