#!/usr/bin/env python3
"""Merge slim MCP batch JSON into search_responses.json."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent
SEARCH = ROOT / "search_responses.json"
GROUPS = json.loads((ROOT / "keywords.json").read_text())["keywords"]


def slim_job(j: dict) -> dict:
    return {k: v for k, v in j.items() if k != "description_snippet"}


def slim_response(resp: dict) -> dict:
    out = {k: v for k, v in resp.items() if k not in ("description_snippet",)}
    if "jobs" in out:
        out["jobs"] = [slim_job(j) for j in out["jobs"]]
    return out


def main() -> None:
    batch = json.loads(sys.stdin.read())
    paired = json.loads(SEARCH.read_text()) if SEARCH.exists() else []
    index = {e["keyword"]: i for i, e in enumerate(paired)}
    for item in batch:
        kw = item["keyword"]
        entry = {
            "keyword": kw,
            "group": GROUPS.get(kw, "OTHER"),
            "response": slim_response(item["response"]),
        }
        if kw in index:
            paired[index[kw]] = entry
        else:
            paired.append(entry)
            index[kw] = len(paired) - 1
    SEARCH.write_text(json.dumps(paired, ensure_ascii=False))
    print(len(paired))


if __name__ == "__main__":
    main()
