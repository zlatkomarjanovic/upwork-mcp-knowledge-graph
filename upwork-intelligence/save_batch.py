#!/usr/bin/env python3
"""Append one keyword search result to a numbered batch file."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main() -> None:
    batch_num = int(sys.argv[1])
    keyword = sys.argv[2]
    group = sys.argv[3]
    resp_path = Path(sys.argv[4])
    resp = json.loads(resp_path.read_text())
    out = ROOT / f"search_batch_{batch_num:03d}.json"
    entries = []
    if out.exists():
        entries = json.loads(out.read_text())
    entries.append({"keyword": keyword, "group": group, "response": resp})
    out.write_text(json.dumps(entries, ensure_ascii=False))


if __name__ == "__main__":
    main()
