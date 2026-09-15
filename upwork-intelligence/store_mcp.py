#!/usr/bin/env python3
"""Store one Upwork find_jobs response: store_mcp.py 'keyword' /path/to/response.json"""
import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent / "mcp_raw"


def slug(kw: str) -> str:
    return re.sub(r"[^\w\- ]", "_", kw)[:80].strip()


def main():
    if len(sys.argv) < 3:
        print("usage: store_mcp.py KEYWORD RESPONSE_JSON_FILE", file=sys.stderr)
        sys.exit(1)
    kw, src = sys.argv[1], Path(sys.argv[2])
    data = json.loads(src.read_text())
    BASE.mkdir(parents=True, exist_ok=True)
    out = BASE / f"{slug(kw)}.json"
    out.write_text(json.dumps({"keyword": kw, "response": data}, ensure_ascii=False))
    print(out)


if __name__ == "__main__":
    main()
