#!/usr/bin/env python3
"""Save a batch of searches from stdin: [{\"keyword\": \"...\", \"response\": {...}}, ...]"""
import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
MCP_RAW = BASE / "mcp_raw"
JSONL = BASE / "search_responses.jsonl"


def slug(kw: str) -> str:
    return re.sub(r"[^\w\- ]", "_", kw)[:80].strip()


def strip_job(job):
    job = dict(job)
    job.pop("description_snippet", None)
    return job


def strip_response(resp):
    resp = dict(resp)
    if "jobs" in resp and resp["jobs"]:
        resp["jobs"] = [strip_job(j) for j in resp["jobs"]]
    return resp


def main():
    batch = json.load(sys.stdin)
    MCP_RAW.mkdir(parents=True, exist_ok=True)
    with JSONL.open("a") as jf:
        for item in batch:
            kw = item["keyword"]
            resp = strip_response(item["response"])
            MCP_RAW.joinpath(f"{slug(kw)}.json").write_text(
                json.dumps({"keyword": kw, "response": resp}, ensure_ascii=False)
            )
            jf.write(json.dumps({"keyword": kw, "response": resp}, ensure_ascii=False) + "\n")
    print(f"saved {len(batch)} keywords")


if __name__ == "__main__":
    main()
