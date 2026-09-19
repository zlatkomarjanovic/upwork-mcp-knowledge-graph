#!/usr/bin/env python3
"""Convert Upwork find_jobs MCP response to keyword payload entry."""
import json
import sys

FIELDS = (
    "url",
    "title",
    "published_date",
    "created_date",
    "job_type",
    "budget",
    "proposals_tier",
    "duration",
    "experience_level",
    "skills",
)


def compact_job(j):
    o = {k: j.get(k) for k in FIELDS if j.get(k) is not None}
    if j.get("client"):
        o["client"] = j["client"]
    return o


def from_mcp(keyword, group, resp):
    if isinstance(resp, str):
        resp = json.loads(resp)
    err = resp.get("error") or resp.get("message")
    if err and "jobs" not in resp:
        if "restricted" in str(err).lower() or "terms of service" in str(err).lower():
            return {"keyword": keyword, "group": group, "ok": False, "jobs": []}
        if resp.get("status") not in (None, "ok"):
            return {"keyword": keyword, "group": group, "ok": False, "jobs": []}
    jobs = [compact_job(j) for j in resp.get("jobs") or []]
    ok = resp.get("status") == "ok" or bool(jobs) or "jobs" in resp
    return {"keyword": keyword, "group": group, "ok": ok, "jobs": jobs}


if __name__ == "__main__":
    keyword, group = sys.argv[1], sys.argv[2]
    resp = json.load(sys.stdin)
    print(json.dumps(from_mcp(keyword, group, resp)))
