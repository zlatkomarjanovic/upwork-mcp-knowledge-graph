#!/usr/bin/env python3
"""Save one Upwork find_jobs response into inbox/ for later merge."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INBOX = ROOT / "inbox"


def slug(kw: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", kw.lower()).strip("_")


def main() -> None:
    kw, group, resp_path = sys.argv[1], sys.argv[2], sys.argv[3]
    resp = json.loads(Path(resp_path).read_text())
    INBOX.mkdir(exist_ok=True)
    entry = {
        "keyword": kw,
        "group": group,
        "jobs": resp.get("jobs") or [],
        "error": resp.get("error") or resp.get("error_code"),
    }
    (INBOX / f"{slug(kw)}.json").write_text(json.dumps(entry, ensure_ascii=False))
    print("ok", kw, len(entry["jobs"]))


if __name__ == "__main__":
    main()
