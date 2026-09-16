#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).parent
CACHE = ROOT / "cache"
CACHE.mkdir(exist_ok=True)


def slim(resp: dict) -> dict:
    jobs = [{k: v for k, v in j.items() if k != "description_snippet"} for j in resp.get("jobs") or []]
    out = {"status": resp.get("status", "ok"), "jobs": jobs}
    if resp.get("error_code"):
        out["error_code"] = resp["error_code"]
    return out


def main() -> None:
    data = json.loads(sys.stdin.read())
    kw = data["keyword"]
    resp = slim(data["response"])
    (CACHE / (quote(kw, safe="") + ".json")).write_text(
        json.dumps({"keyword": kw, "response": resp}, ensure_ascii=False)
    )


if __name__ == "__main__":
    main()
