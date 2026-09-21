#!/usr/bin/env python3
"""Save MCP find_jobs responses to raw_batches/*.json (strips description snippets)."""
import hashlib
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent / "raw_batches"
BASE.mkdir(exist_ok=True)

KEEP_JOB_KEYS = (
    "url", "title", "published_date", "created_date", "budget", "job_type",
    "proposal_count", "duration", "experience_level", "skills", "id", "engagement",
    "freelancers_to_hire", "featured",
)


def compact_job(j):
    out = {k: j.get(k) for k in KEEP_JOB_KEYS if k in j}
    c = j.get("client")
    if c:
        out["client"] = {
            k: c.get(k)
            for k in (
                "country", "rating", "total_posted_jobs", "total_reviews",
                "total_spent", "verification_status",
            )
            if k in c
        }
    return out


def compact_resp(resp):
    if not resp:
        return {"status": "error", "jobs": []}
    jobs = [compact_job(j) for j in (resp.get("jobs") or [])]
    return {"status": resp.get("status", "ok"), "jobs": jobs}


def save_item(keyword, group, response, error=False):
    payload = {
        "keyword": keyword,
        "group": group,
        "response": compact_resp(response),
    }
    if error or payload["response"].get("status") != "ok":
        payload["error"] = True
    slug = hashlib.md5(keyword.encode()).hexdigest()[:12]
    (BASE / f"{slug}.json").write_text(json.dumps(payload, ensure_ascii=False))
    with (BASE / "all.jsonl").open("a") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def main():
    path = Path(sys.argv[1])
    data = json.loads(path.read_text())
    if isinstance(data, dict) and "items" in data:
        items = data["items"]
    elif isinstance(data, list):
        items = data
    else:
        items = [data]
    for item in items:
        save_item(item["keyword"], item["group"], item.get("response") or {}, item.get("error"))
    print(len(items))


if __name__ == "__main__":
    main()
