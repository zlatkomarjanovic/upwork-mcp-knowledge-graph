#!/usr/bin/env python3
import json
import sys
from pathlib import Path

LIVE = Path(__file__).parent / "live_responses.json"


def slim(resp: dict) -> dict:
    jobs = [{k: v for k, v in j.items() if k != "description_snippet"} for j in (resp.get("jobs") or [])]
    out = {"status": resp.get("status", "ok"), "jobs": jobs}
    for k in ("error_code", "error", "trace_id"):
        if k in resp:
            out[k] = resp[k]
    return out


def main() -> None:
    kw = sys.argv[1]
    resp = json.loads(Path(sys.argv[2]).read_text())
    live = json.loads(LIVE.read_text()) if LIVE.exists() else {}
    live[kw] = slim(resp)
    LIVE.write_text(json.dumps(live, ensure_ascii=False))
    print(kw, len(live))


if __name__ == "__main__":
    main()
