#!/usr/bin/env python3
"""
Persist MCP search payloads into mcp_raw/ (agent calls Upwork MCP, then feeds JSON here).

Usage:
  python3 run_all_searches.py --from-ingest /path/to/batch.json
  python3 run_all_searches.py --list-missing

batch.json: {"items":[{"keyword":"...","mcp":{...}}]}
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-ingest", type=Path)
    ap.add_argument("--list-missing", action="store_true")
    args = ap.parse_args()

    if args.from_ingest:
        subprocess.check_call(
            [sys.executable, str(BASE / "ingest_batch.py"), str(args.from_ingest)]
        )
        subprocess.check_call([sys.executable, str(BASE / "build_run_data.py")])
        subprocess.check_call([sys.executable, str(BASE / "process_run.py")])
        return

    if args.list_missing:
        keywords = json.loads((BASE / "keywords.json").read_text())
        raw = BASE / "mcp_raw"
        from save_mcp_raw import slug  # noqa

        missing = [k["keyword"] for k in keywords if not (raw / f"{slug(k['keyword'])}.json").exists()]
        print(json.dumps({"missing": missing, "count": len(missing)}))
        return

    ap.print_help()


if __name__ == "__main__":
    main()
