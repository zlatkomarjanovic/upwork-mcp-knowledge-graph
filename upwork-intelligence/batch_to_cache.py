#!/usr/bin/env python3
"""Write MCP search batch results into cache/*.json."""
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
    for k in ("error_code", "error"):
        if k in resp:
            out[k] = resp[k]
    return out


def main() -> None:
    batch = json.loads(Path(sys.argv[1]).read_text())
    for item in batch:
        kw = item["keyword"]
        resp = slim(item["response"])
        (CACHE / (quote(kw, safe="") + ".json")).write_text(
            json.dumps({"keyword": kw, "response": resp}, ensure_ascii=False)
        )
    print(len(batch))


if __name__ == "__main__":
    main()
