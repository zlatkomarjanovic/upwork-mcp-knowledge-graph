#!/usr/bin/env python3
"""Save one MCP response: quick_save.py KEYWORD RESPONSE_JSON_PATH"""
import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
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
    kw, src = sys.argv[1], Path(sys.argv[2])
    resp = strip_response(json.loads(src.read_text()))
    MCP_RAW.mkdir(parents=True, exist_ok=True)
    data = {"keyword": kw, "response": resp}
    MCP_RAW.joinpath(f"{slug(kw)}.json").write_text(json.dumps(data, ensure_ascii=False))
    with JSONL.open("a") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")
    print("saved", kw)


if __name__ == "__main__":
    main()
