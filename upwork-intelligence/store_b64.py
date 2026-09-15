#!/usr/bin/env python3
"""Store one keyword MCP response from base64 JSON on stdin argv."""
import base64
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from save_batch import slim_item  # noqa: E402

RAW = ROOT / "mcp_raw"
RAW.mkdir(parents=True, exist_ok=True)


def main():
    raw = base64.b64decode(sys.argv[1])
    item = slim_item(json.loads(raw))
    kw = item["keyword"]
    safe = "".join(c if c.isalnum() else "_" for c in kw)[:80]
    (RAW / f"{safe}.json").write_text(json.dumps(item, ensure_ascii=False), encoding="utf-8")
    print(kw)


if __name__ == "__main__":
    main()
