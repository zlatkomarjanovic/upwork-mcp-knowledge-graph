#!/usr/bin/env python3
"""Track keyword search cache coverage and persist MCP batches."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).parent
CACHE = ROOT / "cache"


def keyword_list() -> list[str]:
    return list(json.loads((ROOT / "keywords.json").read_text())["keywords"])


def missing() -> list[str]:
    out = []
    for kw in keyword_list():
        if not (CACHE / f"{quote(kw, safe='')}.json").exists():
            out.append(kw)
    return out


def save_batch(path: Path) -> int:
    from save_batch import slim  # noqa: WPS433

    CACHE.mkdir(exist_ok=True)
    batch = json.loads(path.read_text())
    if isinstance(batch, dict) and "keyword" in batch:
        batch = [batch]
    for item in batch:
        kw = item["keyword"]
        resp = slim(item["response"])
        (CACHE / f"{quote(kw, safe='')}.json").write_text(
            json.dumps({"keyword": kw, "response": resp}, ensure_ascii=False)
        )
    return len(batch)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--missing", action="store_true", help="Print JSON list of keywords without cache")
    p.add_argument("--count-missing", action="store_true")
    p.add_argument("--save", metavar="BATCH_JSON", help="Persist batch file to cache/")
    args = p.parse_args()
    if args.missing:
        print(json.dumps(missing()))
    elif args.count_missing:
        print(len(missing()))
    elif args.save:
        n = save_batch(Path(args.save))
        print(json.dumps({"saved": n, "missing": len(missing())}))
    else:
        p.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
