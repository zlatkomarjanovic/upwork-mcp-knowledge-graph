#!/usr/bin/env python3
"""Write one slimmed keyword response to mcp_raw/."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "mcp_raw"
RAW.mkdir(parents=True, exist_ok=True)

from save_batch import slim_item  # noqa: E402


def main():
    item = slim_item(json.load(sys.stdin))
    kw = item.get("keyword", "unknown")
    safe = "".join(c if c.isalnum() else "_" for c in kw)[:80]
    (RAW / f"{safe}.json").write_text(json.dumps(item, ensure_ascii=False), encoding="utf-8")
    print(kw)


if __name__ == "__main__":
    main()
