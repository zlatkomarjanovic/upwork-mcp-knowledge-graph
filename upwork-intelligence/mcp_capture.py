#!/usr/bin/env python3
"""Capture one Upwork find_jobs MCP JSON response for a keyword. stdin: full MCP JSON object."""
import json, sys
from pathlib import Path

from append_mcp import normalize_row

OUT = Path(__file__).parent / "_batch_results.jsonl"

def main():
    kw = sys.argv[1]
    mcp = json.load(sys.stdin)
    row = normalize_row({"keyword": kw, "response": mcp})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    main()
