#!/usr/bin/env python3
"""Append one keyword search result to raw-searches.json (agent calls MCP, pipes JSON here)."""
import json, sys
from pathlib import Path

BASE = Path(__file__).parent
RAW = BASE / "raw-searches.json"
PROGRESS = BASE / "search-progress.json"


def load_raw():
    if RAW.exists():
        return json.loads(RAW.read_text())
    return {
        "runAt": None,
        "windowHours": 2,
        "searches": [],
        "errors": [],
    }


def main():
    if len(sys.argv) < 3:
        print("Usage: run_searches.py <keyword> <status> [jobs_json_file]", file=sys.stderr)
        sys.exit(1)
    keyword = sys.argv[1]
    status = sys.argv[2]
    jobs = []
    if len(sys.argv) > 3:
        jobs = json.loads(Path(sys.argv[3]).read_text())
    data = load_raw()
    data["searches"] = [s for s in data["searches"] if s.get("keyword") != keyword]
    data["searches"].append({"keyword": keyword, "status": status, "jobs": jobs})
    RAW.write_text(json.dumps(data, indent=2))
    prog = {"completed": []}
    if PROGRESS.exists():
        prog = json.loads(PROGRESS.read_text())
    if status == "ok" and keyword not in prog["completed"]:
        prog["completed"].append(keyword)
    PROGRESS.write_text(json.dumps(prog, indent=2))
    print(json.dumps({"keyword": keyword, "status": status, "jobCount": len(jobs)}))


if __name__ == "__main__":
    main()
