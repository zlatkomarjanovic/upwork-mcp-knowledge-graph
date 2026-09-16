#!/usr/bin/env python3
"""Merge mcp-queue.jsonl into search-raw.json (full keyword list)."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent
QUEUE = ROOT / "mcp-queue.jsonl"
RAW = ROOT / "search-raw.json"
GROUPS = json.loads((ROOT / "keywords.json").read_text())["keywords"]


def slim(resp: dict) -> dict:
    jobs = []
    for j in resp.get("jobs") or []:
        jobs.append({k: v for k, v in j.items() if k != "description_snippet"})
    out = {"status": resp.get("status", "ok"), "jobs": jobs}
    if resp.get("error_code"):
        out["error_code"] = resp["error_code"]
    if resp.get("error"):
        out["error"] = resp["error"]
    return out


def main() -> None:
    by_kw: dict[str, dict] = {}
    if RAW.exists():
        data = json.loads(RAW.read_text())
        for r in data.get("results", []):
            by_kw[r["keyword"]] = r["result"]
    if QUEUE.exists():
        for line in QUEUE.read_text().splitlines():
            if not line.strip():
                continue
            item = json.loads(line)
            kw = item["keyword"]
            by_kw[kw] = slim(item.get("response") or {})
    results = []
    errors = []
    for kw in GROUPS:
        resp = by_kw.get(kw)
        if not resp:
            errors.append(kw)
            resp = {"status": "error", "error_code": "MISSING_SEARCH", "jobs": []}
        elif resp.get("status") != "ok" and not resp.get("jobs"):
            errors.append(kw)
        results.append({"keyword": kw, "result": resp})
    RAW.write_text(json.dumps({"results": results, "errors": errors}, indent=2))
    ok = sum(1 for r in results if r["result"].get("status") == "ok")
    print(json.dumps({"keywords": len(results), "ok": ok, "errors": len(errors)}, indent=2))


if __name__ == "__main__":
    main()
