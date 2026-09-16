#!/usr/bin/env python3
"""Patch one keyword response into search_responses.json."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SEARCH = ROOT / "search_responses.json"


def slim(resp: dict) -> dict:
    jobs = []
    for j in resp.get("jobs") or []:
        jobs.append({k: j[k] for k in j if k != "description_snippet"})
    out = {"status": resp.get("status", "ok"), "jobs": jobs}
    for k in ("error_code", "error", "retry_after_seconds"):
        if k in resp:
            out[k] = resp[k]
    return out


def main() -> None:
    data = json.loads(sys.stdin.read())
    kw = data["keyword"]
    resp = slim(data["response"])
    paired = json.loads(SEARCH.read_text())
    for entry in paired:
        if entry["keyword"] == kw:
            entry["response"] = resp
            break
    else:
        paired.append({"keyword": kw, "group": data.get("group", "OTHER"), "response": resp})
    SEARCH.write_text(json.dumps(paired, indent=2))


if __name__ == "__main__":
    main()
