#!/usr/bin/env python3
"""Flush mcp_queue.jsonl lines into mcp_raw/."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
QUEUE = ROOT / "mcp_queue.jsonl"
RAW = ROOT / "mcp_raw"
RAW.mkdir(parents=True, exist_ok=True)

import sys

sys.path.insert(0, str(ROOT))
from save_batch import slim_item  # noqa: E402


def main():
    if not QUEUE.exists():
        print("no queue")
        return
    n = 0
    for line in QUEUE.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = slim_item(json.loads(line))
        kw = item.get("keyword", "unknown")
        safe = "".join(c if c.isalnum() else "_" for c in kw)[:80]
        (RAW / f"{safe}.json").write_text(json.dumps(item, ensure_ascii=False), encoding="utf-8")
        n += 1
    print(f"flushed {n} keyword responses")


if __name__ == "__main__":
    main()
