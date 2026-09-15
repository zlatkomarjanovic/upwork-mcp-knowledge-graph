#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent / "mcp_raw"
OUT.mkdir(exist_ok=True)


def slug(kw: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", kw.lower()).strip("_") or "kw"


def main():
    raw = sys.stdin.read().strip()
    if not raw:
        return
    item = json.loads(raw)
    kw = item["keyword"]
    resp = item.get("response") or {}
    if isinstance(resp.get("jobs"), list):
        for j in resp["jobs"]:
            if isinstance(j, dict):
                j.pop("description_snippet", None)
    (OUT / f"{slug(kw)}.json").write_text(
        json.dumps({"keyword": kw, "response": resp}, ensure_ascii=False)
    )


if __name__ == "__main__":
    main()
