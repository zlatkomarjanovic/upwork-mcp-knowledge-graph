#!/usr/bin/env python3
"""Write one Upwork find_jobs response to upwork-intelligence/cache/{slug}.json."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upwork-intelligence" / "cache"


def slug(kw: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", kw.lower()).strip("-")


def main() -> int:
    kw = sys.argv[1]
    data = json.loads(Path(sys.argv[2]).read_text())
    ROOT.mkdir(parents=True, exist_ok=True)
    (ROOT / f"{slug(kw)}.json").write_text(json.dumps(data))
    print(slug(kw))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
