#!/usr/bin/env python3
"""
Hourly fetch helper: append one MCP search result to raw-search-batch.jsonl.

Usage (from automation agent after each upwork__find_jobs call):
  python3 run_hourly_fetch.py KEYWORD /path/to/mcp_response.json

Or pipe MCP JSON:
  python3 run_hourly_fetch.py KEYWORD - < response.json

Stores only the jobs array from a successful search response.
"""
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
RAW = BASE / "raw-search-batch.jsonl"


def main():
    if len(sys.argv) < 2:
        print("usage: run_hourly_fetch.py KEYWORD [response.json|-]", file=sys.stderr)
        sys.exit(1)
    keyword = sys.argv[1]
    if len(sys.argv) > 2 and sys.argv[2] != "-":
        data = json.loads(Path(sys.argv[2]).read_text())
    else:
        data = json.load(sys.stdin)
    jobs = data.get("jobs", []) if isinstance(data, dict) else []
    err = data.get("error") or data.get("reason") if isinstance(data, dict) else None
    if data.get("status") == "error" or data.get("error_code"):
        line = {"keyword": keyword, "jobs": [], "error": data.get("reason") or data.get("error_code")}
    else:
        line = {"keyword": keyword, "jobs": jobs}
    with RAW.open("a") as f:
        f.write(json.dumps(line, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
