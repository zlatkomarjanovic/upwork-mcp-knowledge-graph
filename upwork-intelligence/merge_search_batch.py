#!/usr/bin/env python3
"""Merge MCP batch into search_responses.json (slim jobs, no description_snippet)."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent
OUT = ROOT / "search_responses.json"
KW = json.loads((ROOT / "keywords.json").read_text())["keywords"]


def slim(resp: dict) -> dict:
    jobs = []
    for j in resp.get("jobs") or []:
        jobs.append({k: v for k, v in j.items() if k != "description_snippet"})
    o = {"status": resp.get("status", "ok"), "jobs": jobs}
    if resp.get("error_code"):
        o["error_code"] = resp["error_code"]
    if resp.get("error"):
        o["error"] = resp["error"]
    return o


def main():
    batch_path = Path(sys.argv[1])
    batch = json.loads(batch_path.read_text())
    by_kw = {}
    if OUT.exists():
        for e in json.loads(OUT.read_text()):
            by_kw[e["keyword"]] = e
    for item in batch:
        kw = item["keyword"]
        group = item.get("group") or KW.get(kw, "UNKNOWN")
        resp = item.get("response") or {}
        if resp.get("status") == "error" or resp.get("error_code"):
            by_kw[kw] = {"keyword": kw, "group": group, "response": resp}
        else:
            by_kw[kw] = {"keyword": kw, "group": group, "response": slim(resp)}
    OUT.write_text(json.dumps(list(by_kw.values()), indent=2))
    print(json.dumps({"count": len(by_kw)}))


if __name__ == "__main__":
    main()
