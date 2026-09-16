#!/usr/bin/env python3
import json
import sys


def slim(resp: dict) -> dict:
    jobs = []
    for j in resp.get("jobs") or []:
        jobs.append({k: v for k, v in j.items() if k != "description_snippet"})
    out = {"status": resp.get("status", "ok"), "jobs": jobs}
    if resp.get("error_code"):
        out["error_code"] = resp["error_code"]
    return out


if __name__ == "__main__":
    print(json.dumps(slim(json.loads(sys.stdin.read()))))
