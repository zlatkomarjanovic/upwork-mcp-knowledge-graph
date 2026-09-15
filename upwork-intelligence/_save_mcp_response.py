#!/usr/bin/env python3
"""Save one MCP find_jobs response. Usage: _save_mcp_response.py KEYWORD GROUP path/to/response.json"""
import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
RESP = BASE / "_batches" / "responses"


def slug(kw: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", kw.lower()).strip("_")


def main():
    kw, group, resp_path = sys.argv[1:4]
    resp = json.loads(Path(resp_path).read_text())
    RESP.mkdir(parents=True, exist_ok=True)
    out = RESP / f"{slug(kw)}.json"
    out.write_text(json.dumps(resp, ensure_ascii=False))


if __name__ == "__main__":
    main()
