#!/usr/bin/env python3
"""Extract upwork__find_jobs results from a cloud agent transcript.json into mcp_queue/."""
import hashlib
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
QUEUE = BASE / "mcp_queue"
QUEUE.mkdir(exist_ok=True)

import importlib.machinery
from importlib.util import module_from_spec, spec_from_loader

_loader = importlib.machinery.SourceFileLoader("proc", str(BASE / ".run_process.py"))
_spec = spec_from_loader("proc", _loader)
proc = module_from_spec(_spec)
_loader.exec_module(proc)

kw_to_group = {}
for g, kws in proc.KEYWORD_GROUPS.items():
    for kw in kws:
        kw_to_group[kw] = g

ORDERED = [kw for g, kws in proc.KEYWORD_GROUPS.items() for kw in kws]


def slug(kw):
    return hashlib.md5(kw.encode()).hexdigest()[:12]


def compact_job(j):
    keep = (
        "url", "title", "published_date", "created_date", "budget", "job_type",
        "proposal_count", "duration", "experience_level", "skills", "id", "engagement", "featured",
    )
    out = {k: j.get(k) for k in keep if k in j}
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


def iter_find_jobs_results(transcript):
    for msg in transcript.get("messages", []):
        if msg.get("role") != "tool":
            continue
        tr = msg.get("tool_result") or {}
        val = tr.get("value") or {}
        if val.get("selectedTool") != "upwork__find_jobs":
            continue
        raw = val.get("result")
        if not raw:
            continue
        try:
            resp = json.loads(raw) if isinstance(raw, str) else raw
        except json.JSONDecodeError:
            continue
        if resp.get("status") == "ok" and "jobs" in resp:
            yield resp


def main():
    path = Path(sys.argv[1])
    transcript = json.loads(path.read_text())
    results = list(iter_find_jobs_results(transcript))
    saved = 0
    for i, resp in enumerate(results):
        if i >= len(ORDERED):
            break
        kw = ORDERED[i]
        compact = {"status": "ok", "jobs": [compact_job(j) for j in resp.get("jobs") or []]}
        group = kw_to_group.get(kw, "UNKNOWN")
        payload = {"keyword": kw, "group": group, "response": compact}
        (QUEUE / f"{slug(kw)}.json").write_text(json.dumps(payload, ensure_ascii=False))
        saved += 1
    print(json.dumps({"extracted": saved, "results_in_transcript": len(results)}))


if __name__ == "__main__":
    main()
