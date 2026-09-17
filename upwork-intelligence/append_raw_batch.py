#!/usr/bin/env python3
"""Append slim MCP search results from stdin JSON array [{keyword, response|mcp, error?}]."""
import json
import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).parent
RAW = ROOT / "raw_search_results.json"
CACHE = ROOT / "cache"
CACHE.mkdir(exist_ok=True)


def slim(resp: dict) -> dict:
    jobs = [{k: v for k, v in j.items() if k != "description_snippet"} for j in (resp.get("jobs") or [])]
    out = {"status": resp.get("status", "ok"), "jobs": jobs}
    for k in ("error_code", "error"):
        if k in resp:
            out[k] = resp[k]
    return out


def main() -> None:
    batch = json.loads(sys.stdin.read())
    data = json.loads(RAW.read_text()) if RAW.exists() else {"searches": [], "errors": []}
    done = {s["keyword"] for s in data["searches"]}
    errors = set(data.get("errors") or [])
    for item in batch:
        kw = item["keyword"]
        done.discard(kw)
        errors.discard(kw)
        if item.get("error"):
            errors.add(kw)
            continue
        resp = item.get("response") or item.get("mcp") or {}
        if resp.get("status") == "error" or resp.get("error_code"):
            errors.add(kw)
            continue
        slimmed = slim(resp)
        data["searches"] = [s for s in data["searches"] if s["keyword"] != kw]
        data["searches"].append({"keyword": kw, "response": slimmed})
        (CACHE / (quote(kw, safe="") + ".json")).write_text(
            json.dumps({"keyword": kw, "response": slimmed}, ensure_ascii=False)
        )
    data["errors"] = sorted(errors)
    RAW.write_text(json.dumps(data, ensure_ascii=False))
    print(len(data["searches"]), "cached", len(data["errors"]), "errors")


if __name__ == "__main__":
    main()
