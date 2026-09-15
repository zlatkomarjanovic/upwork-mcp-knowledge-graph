#!/usr/bin/env python3
"""Write pending.json responses into mcp_raw + search_responses.jsonl"""
import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
PENDING = BASE / "pending.json"
MCP_RAW = BASE / "mcp_raw"
JSONL = BASE / "search_responses.jsonl"


def slug(kw: str) -> str:
    return re.sub(r"[^\w\- ]", "_", kw)[:80].strip()


def strip_response(resp):
    resp = dict(resp)
    jobs = resp.get("jobs")
    if jobs:
        out = []
        for j in jobs:
            j = dict(j)
            j.pop("description_snippet", None)
            out.append(j)
        resp["jobs"] = out
    return resp


def main():
    if not PENDING.exists():
        print("no pending.json")
        sys.exit(1)
    data = json.loads(PENDING.read_text())
    items = data.get("responses") or []
    MCP_RAW.mkdir(parents=True, exist_ok=True)
    with JSONL.open("a") as jf:
        for item in items:
            kw = item["keyword"]
            resp = strip_response(item["response"])
            blob = {"keyword": kw, "response": resp}
            MCP_RAW.joinpath(f"{slug(kw)}.json").write_text(json.dumps(blob, ensure_ascii=False))
            jf.write(json.dumps(blob, ensure_ascii=False) + "\n")
    print(f"flushed {len(items)} keywords")


if __name__ == "__main__":
    main()
