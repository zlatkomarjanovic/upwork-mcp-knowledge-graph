#!/usr/bin/env python3
"""Append or update one keyword result in search-raw.json."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent
RAW = ROOT / "search-raw.json"


def slim(resp: dict) -> dict:
    jobs = []
    for j in resp.get("jobs") or []:
        jobs.append({k: v for k, v in j.items() if k != "description_snippet"})
    out = {"status": resp.get("status", "ok"), "jobs": jobs}
    if resp.get("error_code"):
        out["error_code"] = resp["error_code"]
    return out


def main():
    item = json.loads(sys.stdin.read())
    kw = item["keyword"]
    resp = slim(item["response"])
    data = {"results": [], "errors": []}
    if RAW.exists():
        data = json.loads(RAW.read_text())
    idx = {r["keyword"]: i for i, r in enumerate(data["results"])}
    entry = {"keyword": kw, "result": resp}
    if kw in idx:
        data["results"][idx[kw]] = entry
    else:
        data["results"].append(entry)
    if resp.get("status") != "ok" and not resp.get("jobs"):
        if kw not in data["errors"]:
            data["errors"].append(kw)
    RAW.write_text(json.dumps(data, indent=2))
    print(len(data["results"]))


if __name__ == "__main__":
    main()
