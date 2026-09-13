#!/usr/bin/env python3
"""Read JSON array of {keyword, group, response} from path; save via save_mcp_compact."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from save_mcp_compact import save_item  # noqa: E402


def main():
    path = Path(sys.argv[1])
    items = json.loads(path.read_text())
    if isinstance(items, dict):
        items = items.get("items", [])
    for item in items:
        save_item(
            item["keyword"],
            item["group"],
            item.get("response") or {},
            item.get("error", False),
        )
    print(len(items))


if __name__ == "__main__":
    main()
