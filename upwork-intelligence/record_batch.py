#!/usr/bin/env python3
"""Persist batch file [{keyword, response}, ...] to mcp_raw + search_responses.jsonl"""
import json
import sys
from pathlib import Path

from quick_save import strip_response, slug  # noqa: E402

BASE = Path(__file__).resolve().parent
MCP_RAW = BASE / "mcp_raw"
JSONL = BASE / "search_responses.jsonl"


def save_item(kw, resp):
    resp = strip_response(resp)
    blob = {"keyword": kw, "response": resp}
    MCP_RAW.mkdir(parents=True, exist_ok=True)
    MCP_RAW.joinpath(f"{slug(kw)}.json").write_text(json.dumps(blob, ensure_ascii=False))
    with JSONL.open("a") as f:
        f.write(json.dumps(blob, ensure_ascii=False) + "\n")


def main():
    path = Path(sys.argv[1])
    batch = json.loads(path.read_text())
    for item in batch:
        save_item(item["keyword"], item["response"])
    print("saved", len(batch))


if __name__ == "__main__":
    main()
