#!/usr/bin/env python3
"""Append slim MCP search batch to raw_search_results.json."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent
RAW = ROOT / "raw_search_results.json"


def slim(resp: dict) -> dict:
    jobs = []
    for j in resp.get("jobs") or []:
        jobs.append({k: v for k, v in j.items() if k != "description_snippet"})
    out = {"status": resp.get("status", "ok"), "jobs": jobs}
    for k in ("error_code", "error"):
        if k in resp:
            out[k] = resp[k]
    return out


def main() -> None:
    batch = json.loads(Path(sys.argv[1]).read_text())
    data: dict = {"searches": [], "errors": []}
    if RAW.exists():
        data = json.loads(RAW.read_text())
    by_kw = {s["keyword"]: s for s in data.get("searches", [])}
    for item in batch:
        kw = item["keyword"]
        resp = item["response"]
        if resp.get("status") == "error" or resp.get("error_code"):
            if kw not in data["errors"]:
                data["errors"].append(kw)
            continue
        by_kw[kw] = {"keyword": kw, "response": slim(resp)}
    data["searches"] = list(by_kw.values())
    RAW.write_text(json.dumps(data, indent=2))
    print(json.dumps({"searches": len(data["searches"]), "errors": len(data["errors"])}))


if __name__ == "__main__":
    main()
