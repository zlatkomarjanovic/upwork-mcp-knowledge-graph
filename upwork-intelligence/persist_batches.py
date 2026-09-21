#!/usr/bin/env python3
"""Write MCP search results to raw_batches/*.json for .run_process.py."""
import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).parent
RAW = BASE / "raw_batches"
RAW.mkdir(exist_ok=True)

GROUPS = {}
try:
    meta = json.loads((BASE / "keywords.json").read_text())
    GROUPS = meta.get("keywords") or {}
except OSError:
    pass

if not GROUPS:
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "run_process", BASE / ".run_process.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    GROUPS = mod.KW_TO_GROUP


def slug(kw: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", kw.lower()).strip("_")
    return s[:80] or "kw"


def save_one(keyword: str, resp: dict, group: str | None = None) -> None:
    g = group or GROUPS.get(keyword, "OTHER")
    if resp.get("status") == "error" or resp.get("error"):
        payload = {"keyword": keyword, "group": g, "error": resp.get("error") or resp.get("error_code")}
    else:
        payload = {"keyword": keyword, "group": g, "jobs": resp.get("jobs") or []}
    (RAW / f"{slug(keyword)}.json").write_text(json.dumps(payload, ensure_ascii=False))


def main():
    data = json.loads(sys.stdin.read())
    items = data if isinstance(data, list) else data.get("batch") or [data]
    for item in items:
        kw = item["keyword"]
        resp = item.get("response") or item
        if "jobs" in item and "response" not in item:
            resp = item
        save_one(kw, resp, item.get("group"))
    print(len(list(RAW.glob("*.json"))))


if __name__ == "__main__":
    main()
