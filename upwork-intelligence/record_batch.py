#!/usr/bin/env python3
import json
import sys
from pathlib import Path

BASE = Path(__file__).parent
RAW = BASE / "raw_search_results.json"


def slim(resp: dict) -> dict:
    jobs = []
    for j in resp.get("jobs") or []:
        jobs.append({k: j[k] for k in j if k != "description_snippet"})
    out = {"status": resp.get("status", "ok"), "jobs": jobs}
    if resp.get("error"):
        out["error"] = resp["error"]
    if resp.get("error_code"):
        out["error_code"] = resp["error_code"]
    return out


def main():
    items = json.loads(sys.stdin.read())
    data = {"searches": [], "errors": []}
    if RAW.exists():
        data = json.loads(RAW.read_text())
    seen = {s["keyword"] for s in data["searches"]}
    for item in items:
        kw = item["keyword"]
        if "error" in item and item["error"]:
            if kw not in data["errors"]:
                data["errors"].append(kw)
            continue
        resp = slim(item.get("response") or {})
        if resp.get("status") == "error" or resp.get("error"):
            if kw not in data["errors"]:
                data["errors"].append(kw)
            continue
        entry = {"keyword": kw, "response": resp}
        if kw in seen:
            for i, s in enumerate(data["searches"]):
                if s["keyword"] == kw:
                    data["searches"][i] = entry
                    break
        else:
            data["searches"].append(entry)
            seen.add(kw)
    RAW.write_text(json.dumps(data, ensure_ascii=False))
    print(json.dumps({"searches": len(data["searches"]), "errors": len(data["errors"])}))


if __name__ == "__main__":
    main()
