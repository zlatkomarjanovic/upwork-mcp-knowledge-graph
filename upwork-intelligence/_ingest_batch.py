#!/usr/bin/env python3
"""Ingest batch JSON [{keyword, group, response}] into SQLite store."""
import json
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
TMP = BASE / "_batches" / "tmp"
TMP.mkdir(parents=True, exist_ok=True)


def main():
    data = json.loads(Path(sys.argv[1]).read_text())
    for item in data:
        p = TMP / "one.json"
        p.write_text(json.dumps(item["response"], ensure_ascii=False))
        subprocess.check_call(
            [
                sys.executable,
                str(BASE / "_mcp_sqlite_store.py"),
                item["keyword"],
                item["group"],
                str(p),
            ]
        )
    print("ingested", len(data))


if __name__ == "__main__":
    main()
