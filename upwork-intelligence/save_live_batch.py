#!/usr/bin/env python3
"""Save live MCP batch: save_live_batch.py BATCH.json (items: keyword, group, response)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from save_mcp_compact import save_item  # noqa: E402

def main():
    items = json.loads(Path(sys.argv[1]).read_text())
    groups = json.loads((Path(__file__).resolve().parent / "keyword_to_group.json").read_text())
    for item in items:
        kw = item["keyword"]
        group = item.get("group") or groups[kw]
        save_item(kw, group, item.get("response") or {}, item.get("error", False))
    print("saved", len(items))

if __name__ == "__main__":
    main()
