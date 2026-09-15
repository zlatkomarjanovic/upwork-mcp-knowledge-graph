#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).parent
CACHE = ROOT / "cache"
CACHE.mkdir(exist_ok=True)


def slim(resp: dict) -> dict:
    jobs = []
    for j in resp.get("jobs") or []:
        jobs.append({k: j[k] for k in j if k != "description_snippet"})
    out = {"status": resp.get("status", "ok"), "jobs": jobs}
    for k in ("error_code", "error"):
        if k in resp:
            out[k] = resp[k]
    return out


def main():
    data = json.loads(sys.stdin.read())
    kw = data["keyword"]
    path = CACHE / (quote(kw, safe="") + ".json")
    path.write_text(
        json.dumps({"keyword": kw, "response": slim(data["response"])}, ensure_ascii=False)
    )


if __name__ == "__main__":
    main()
