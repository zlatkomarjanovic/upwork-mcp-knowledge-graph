#!/usr/bin/env python3
"""Merge raw_search_results.json entries into search_responses.json."""
import json
from pathlib import Path

ROOT = Path(__file__).parent
SEARCH = ROOT / "search_responses.json"
RAW = ROOT / "raw_search_results.json"
GROUPS = json.loads((ROOT / "keywords.json").read_text())["keywords"]


def slim(resp: dict) -> dict:
    jobs = []
    for j in resp.get("jobs") or []:
        jobs.append({k: v for k, v in j.items() if k != "description_snippet"})
    out = {"status": resp.get("status", "ok"), "jobs": jobs}
    for k in ("error_code", "error"):
        if k in resp:
            out[k] = resp[k]
    return out


def main():
    paired = json.loads(SEARCH.read_text()) if SEARCH.exists() else []
    index = {e["keyword"]: i for i, e in enumerate(paired)}
    if not index:
        paired = [{"keyword": k, "group": g, "response": {"status": "error", "error_code": "NOT_SEARCHED"}} for k, g in GROUPS.items()]
        index = {e["keyword"]: i for i, e in enumerate(paired)}

    if RAW.exists():
        data = json.loads(RAW.read_text())
        for item in data.get("searches", []):
            kw = item["keyword"]
            entry = {"keyword": kw, "group": GROUPS.get(kw, "OTHER"), "response": slim(item["response"])}
            if kw in index:
                paired[index[kw]] = entry
            else:
                paired.append(entry)
                index[kw] = len(paired) - 1

    SEARCH.write_text(json.dumps(paired, indent=2))
    ok = sum(1 for p in paired if p.get("response", {}).get("status") == "ok")
    err = sum(1 for p in paired if p.get("response", {}).get("error_code"))
    print(json.dumps({"keywords": len(paired), "ok": ok, "errors": err}))


if __name__ == "__main__":
    main()
