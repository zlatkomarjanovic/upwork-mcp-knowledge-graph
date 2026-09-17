#!/usr/bin/env python3
"""Append one batch file (JSON array) to _batch_results.jsonl via record_searches."""
import json
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
RECORD = BASE / "record_searches.py"


def main():
    path = Path(sys.argv[1])
    data = json.loads(path.read_text())
    subprocess.run(
        [sys.executable, str(RECORD)],
        input=json.dumps(data),
        text=True,
        check=True,
    )


if __name__ == "__main__":
    main()
