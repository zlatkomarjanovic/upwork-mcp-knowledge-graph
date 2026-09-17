#!/usr/bin/env python3
"""Save MCP batch results into cache/ (record_search format)."""
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
        jobs.append({k: v for k, v in j.items() if k != "description_snippet"})
    out = {"status": resp.get("status", "ok"), "jobs": jobs}
    for k in ("error_code", "error", "message"):
        if k in resp:
            out[k] = resp[k]
    if resp.get("status") == "error":
        out["status"] = "error"
    return out


def main() -> None:
    batch = json.loads(Path(sys.argv[1]).read_text())
    for item in batch:
        kw = item["keyword"]
        path = CACHE / f"{quote(kw, safe='')}.json"
        path.write_text(
            json.dumps({"keyword": kw, "response": slim(item["response"])}, ensure_ascii=False)
        )
    print(len(batch))


if __name__ == "__main__":
    main()
