#!/usr/bin/env python3
"""Write wave JSON array entries into inbox/{slug}.json"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INBOX = ROOT / "inbox"
INBOX.mkdir(exist_ok=True)


def slug(kw: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", kw.lower()).strip("_")


def main() -> None:
    wave = json.loads(Path(sys.argv[1]).read_text())
    for e in wave:
        kw = e["keyword"]
        out = {
            "keyword": kw,
            "group": e["group"],
            "jobs": e.get("jobs") or (e.get("response") or {}).get("jobs") or [],
            "error": e.get("error") or (e.get("response") or {}).get("error_code"),
        }
        (INBOX / f"{slug(kw)}.json").write_text(json.dumps(out, ensure_ascii=False))
    print(len(wave))


if __name__ == "__main__":
    main()
