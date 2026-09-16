#!/usr/bin/env python3
"""Build _search_batches.jsonl from mcp_cache/ + keywords.json order."""
import json
from pathlib import Path

BASE = Path(__file__).parent
CACHE = BASE / "mcp_cache"
BATCH = BASE / "_search_batches.jsonl"
KEYWORDS = list(json.loads((BASE / "keywords.json").read_text())["keywords"].keys())


def slug(kw: str) -> str:
    import re

    return re.sub(r"[^a-z0-9]+", "_", kw.lower()).strip("_")


def main():
    fallback = {}
    if BATCH.exists():
        for line in BATCH.read_text().splitlines():
            if line.strip():
                o = json.loads(line)
                fallback[o["keyword"]] = line.strip()

    lines = []
    missing = []
    for kw in KEYWORDS:
        p = CACHE / f"{slug(kw)}.json"
        if p.exists():
            lines.append(p.read_text().strip())
        elif kw in fallback:
            lines.append(fallback[kw])
        else:
            missing.append(kw)
            lines.append(json.dumps({"keyword": kw, "error": True}, ensure_ascii=False))
    BATCH.write_text("\n".join(lines) + "\n")
    print(json.dumps({"lines": len(lines), "missing": len(missing), "missing_sample": missing[:5]}))


if __name__ == "__main__":
    main()
