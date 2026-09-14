#!/usr/bin/env python3
"""Save one MCP find_jobs response to mcp_queue and raw_batches."""
import hashlib
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
from save_mcp_compact import save_item  # noqa: E402

QUEUE = BASE / "mcp_queue"
QUEUE.mkdir(exist_ok=True)


def strip_snippets(resp):
    if not resp:
        return {"status": "error", "jobs": []}
    out = dict(resp)
    jobs = []
    for j in out.get("jobs") or []:
        jj = dict(j)
        jj.pop("description_snippet", None)
        jobs.append(jj)
    out["jobs"] = jobs
    return out


def save_one(keyword, group, response, error=False):
    resp = strip_snippets(response)
    payload = {"keyword": keyword, "group": group, "response": resp}
    if error or resp.get("status") == "error":
        payload["error"] = True
    slug = hashlib.md5(keyword.encode()).hexdigest()[:12]
    (QUEUE / f"{slug}.json").write_text(json.dumps(payload, ensure_ascii=False))
    save_item(keyword, group, resp, payload.get("error", False))
    return len(resp.get("jobs") or [])


def main():
    if len(sys.argv) >= 4:
        path = Path(sys.argv[3])
        resp = json.loads(path.read_text())
        n = save_one(sys.argv[1], sys.argv[2], resp)
        print(keyword := sys.argv[1], n)
        return
    items = json.loads(Path(sys.argv[1]).read_text())
    if isinstance(items, dict):
        items = items.get("items", [])
    total = 0
    for item in items:
        total += save_one(
            item["keyword"],
            item.get("group") or "UNKNOWN",
            item.get("response") or {},
            item.get("error", False),
        )
    print("saved", len(items), "jobs_total", total)


if __name__ == "__main__":
    main()
