#!/usr/bin/env python3
"""Merge keyword search lines into search_responses.json."""
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
    if resp.get("error"):
        out["error"] = resp["error"]
    return out


def main():
    path = Path(sys.argv[1])
    paired = json.loads(SEARCH.read_text()) if SEARCH.exists() else []
    index = {e["keyword"]: i for i, e in enumerate(paired)}
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        kw = item["keyword"]
        entry = {
            "keyword": kw,
            "group": GROUPS.get(kw, "OTHER"),
            "response": slim(item["response"]),
        }
        if kw in index:
            paired[index[kw]] = entry
        else:
            paired.append(entry)
            index[kw] = len(paired) - 1
    paired.sort(key=lambda x: list(GROUPS.keys()).index(x["keyword"]) if x["keyword"] in GROUPS else 999)
    SEARCH.write_text(json.dumps(paired, indent=2))
    print(len(paired))


if __name__ == "__main__":
    main()
