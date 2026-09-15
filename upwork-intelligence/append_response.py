#!/usr/bin/env python3
"""Append one search response line: append_response.py KEYWORD RESPONSE_JSON_FILE"""
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
OUT = BASE / "search_responses.jsonl"
MCP_RAW = BASE / "mcp_raw"


def slug(kw: str) -> str:
    import re

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
    kw, src = sys.argv[1], Path(sys.argv[2])
    resp = strip_response(json.loads(src.read_text()))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    MCP_RAW.mkdir(parents=True, exist_ok=True)
    blob = {"keyword": kw, "response": resp}
    with OUT.open("a") as f:
        f.write(json.dumps(blob, ensure_ascii=False) + "\n")
    MCP_RAW.joinpath(f"{slug(kw)}.json").write_text(json.dumps(blob, ensure_ascii=False))
    print("ok", kw)


if __name__ == "__main__":
    main()
