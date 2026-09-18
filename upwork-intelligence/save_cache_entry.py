#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).parent
CACHE = ROOT / "cache"
CACHE.mkdir(exist_ok=True)


def slim_job(j: dict) -> dict:
    return {k: v for k, v in j.items() if k != "description_snippet"}


def slim_response(resp: dict) -> dict:
    out = dict(resp)
    if "jobs" in out:
        out["jobs"] = [slim_job(j) for j in out["jobs"]]
    return out


def main() -> None:
    data = json.loads(sys.stdin.read())
    kw = data["keyword"]
    resp = slim_response(data["response"])
    path = CACHE / (quote(kw, safe="") + ".json")
    path.write_text(json.dumps({"keyword": kw, "response": resp}, ensure_ascii=False))


if __name__ == "__main__":
    main()
