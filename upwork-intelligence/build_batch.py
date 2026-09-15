#!/usr/bin/env python3
"""Build mcp_batch.json from mcp_queue/*.json fragments written per search."""
import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent
QUEUE = BASE / "mcp_queue"
OUT = BASE / "mcp_batch.json"

from process_run import ALL_KEYWORDS, KW_TO_GROUP  # noqa: E402


def slug(kw: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", kw.lower()).strip("-")[:80]


def main():
    by_kw = {}
    if QUEUE.exists():
        for p in QUEUE.glob("*.json"):
            try:
                entry = json.loads(p.read_text())
                kw = entry.get("keyword")
                if kw:
                    by_kw[kw] = entry
            except json.JSONDecodeError:
                pass
    entries = []
    for kw in ALL_KEYWORDS:
        if kw in by_kw:
            entries.append(by_kw[kw])
        else:
            entries.append(
                {"keyword": kw, "group": KW_TO_GROUP.get(kw, ""), "error": "search_not_run"}
            )
    OUT.write_text(json.dumps(entries, ensure_ascii=False, indent=2))
    print(len(entries), "entries (", sum(1 for e in entries if not e.get("error")), "ok ) ->", OUT)

if __name__ == "__main__":
    main()
