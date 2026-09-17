#!/usr/bin/env python3
"""Merge MCP batch results into search_responses.json."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent
SEARCH = ROOT / "search_responses.json"
GROUPS = json.loads((ROOT / "keywords.json").read_text())["keywords"]


def slim_response(resp: dict) -> dict:
    out = dict(resp)
    jobs = []
    for j in out.get("jobs") or []:
        jj = {k: v for k, v in j.items() if k != "description_snippet"}
        jobs.append(jj)
    out["jobs"] = jobs
    return out


def main() -> None:
    batch = json.loads(Path(sys.argv[1]).read_text())
    paired = json.loads(SEARCH.read_text()) if SEARCH.exists() else []
    index = {e["keyword"]: i for i, e in enumerate(paired)}
    for item in batch:
        kw = item["keyword"]
        entry = {
            "keyword": kw,
            "group": GROUPS.get(kw, "OTHER"),
            "response": slim_response(item.get("response") or {}),
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
