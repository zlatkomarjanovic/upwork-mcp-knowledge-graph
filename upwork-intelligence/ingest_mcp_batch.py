#!/usr/bin/env python3
"""Ingest MCP batch JSON into cache and search_responses.json."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).parent
CACHE = ROOT / "cache"
SEARCH = ROOT / "search_responses.json"
GROUPS = json.loads((ROOT / "keywords.json").read_text())["keywords"]


def slim(resp: dict) -> dict:
    jobs = [{k: v for k, v in j.items() if k != "description_snippet"} for j in resp.get("jobs") or []]
    out = {"status": resp.get("status", "ok"), "jobs": jobs}
    for k in ("error", "error_code"):
        if k in resp:
            out[k] = resp[k]
    return out


def main() -> None:
    batch = json.loads(Path(sys.argv[1]).read_text())
    CACHE.mkdir(exist_ok=True)
    paired = json.loads(SEARCH.read_text()) if SEARCH.exists() else []
    index = {e["keyword"]: i for i, e in enumerate(paired)}
    for item in batch:
        kw = item["keyword"]
        resp = slim(item.get("response") or {})
        (CACHE / (quote(kw, safe="") + ".json")).write_text(
            json.dumps({"keyword": kw, "response": resp}, ensure_ascii=False)
        )
        entry = {"keyword": kw, "group": GROUPS.get(kw, "OTHER"), "response": resp}
        if kw in index:
            paired[index[kw]] = entry
        else:
            paired.append(entry)
            index[kw] = len(paired) - 1
    paired.sort(key=lambda x: list(GROUPS.keys()).index(x["keyword"]))
    SEARCH.write_text(json.dumps(paired, indent=2))
    print(json.dumps({"ingested": len(batch), "total": len(paired)}))


if __name__ == "__main__":
    main()
