#!/usr/bin/env python3
"""Persist batch items from JSON file: [{keyword, group?, response}]. Updates cache + raw_batches."""
import json
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent


def main():
    path = Path(sys.argv[1])
    items = json.loads(path.read_text())
    if isinstance(items, dict):
        items = items.get("items", [items])
    for item in items:
        kw = item["keyword"]
        group = item.get("group") or "UNKNOWN"
        resp = item.get("response") or {}
        subprocess.run(
            [sys.executable, str(BASE / "persist_kw.py"), kw, group],
            input=json.dumps(resp),
            text=True,
            check=True,
            cwd=str(BASE),
        )
        cache_path = BASE / "mcp_cache.json"
        cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}
        cache[kw] = resp
        cache_path.write_text(json.dumps(cache, ensure_ascii=False))
    print(json.dumps({"persisted": len(items)}))


if __name__ == "__main__":
    main()
