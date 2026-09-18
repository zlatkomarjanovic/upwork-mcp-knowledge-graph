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
    out = {k: v for k, v in resp.items() if k != "description_snippet"}
    if "jobs" in out:
        out["jobs"] = [slim_job(j) for j in out["jobs"]]
    return out


def main() -> None:
    batch = json.loads(sys.stdin.read())
    for item in batch:
        kw = item["keyword"]
        path = CACHE / (quote(kw, safe="") + ".json")
        path.write_text(
            json.dumps(
                {"keyword": kw, "response": slim_response(item["response"])},
                ensure_ascii=False,
            )
        )
    print(len(batch))


if __name__ == "__main__":
    main()
