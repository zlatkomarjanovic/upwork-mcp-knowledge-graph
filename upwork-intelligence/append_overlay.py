#!/usr/bin/env python3
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent
OVERLAY = ROOT / "live_search_overlay.json"


def slim(resp: dict) -> dict:
    jobs = [{k: j[k] for k in j if k != "description_snippet"} for j in resp.get("jobs") or []]
    out = {"status": resp.get("status", "ok"), "jobs": jobs}
    for k in ("error_code", "error"):
        if k in resp:
            out[k] = resp[k]
    return out


def main() -> None:
    items = json.loads(sys.stdin.read())
    data = json.loads(OVERLAY.read_text()) if OVERLAY.exists() else {}
    for item in items:
        data[item["keyword"]] = slim(item["response"])
    OVERLAY.write_text(json.dumps(data, indent=2))
    print(len(data))


if __name__ == "__main__":
    main()
