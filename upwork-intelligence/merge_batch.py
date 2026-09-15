#!/usr/bin/env python3
"""Merge a batch JSON array into mcp_raw/ via save_batch slimming."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from save_batch import slim_item  # noqa: E402

RAW = ROOT / "mcp_raw"
RAW.mkdir(parents=True, exist_ok=True)


def main():
    path = Path(sys.argv[1])
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        data = [data]
    for item in data:
        item = slim_item(item)
        kw = item.get("keyword", "unknown")
        safe = "".join(c if c.isalnum() else "_" for c in kw)[:80]
        (RAW / f"{safe}.json").write_text(json.dumps(item, ensure_ascii=False), encoding="utf-8")
    print(f"merged {len(data)} keywords into mcp_raw")


if __name__ == "__main__":
    main()
