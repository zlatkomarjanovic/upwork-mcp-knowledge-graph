#!/usr/bin/env python3
"""Append batch of {keyword: response} into live_responses.json from stdin."""
import json
import sys
from pathlib import Path

LIVE = Path(__file__).parent / "live_responses.json"


def slim(resp: dict) -> dict:
    jobs = []
    for j in resp.get("jobs") or []:
        jobs.append({k: v for k, v in j.items() if k != "description_snippet"})
    out = {"status": resp.get("status", "ok"), "jobs": jobs}
    for k in ("error_code", "error", "trace_id"):
        if k in resp:
            out[k] = resp[k]
    return out


def main() -> None:
    batch = json.loads(sys.stdin.read())
    live = json.loads(LIVE.read_text()) if LIVE.exists() else {}
    for kw, resp in batch.items():
        live[kw] = slim(resp)
    LIVE.write_text(json.dumps(live, ensure_ascii=False))
    print(len(live))


if __name__ == "__main__":
    main()
