#!/usr/bin/env python3
"""
Extract Upwork find_jobs results from agent transcript JSON (batch-fetch-details output).
Usage: merge_transcript_mcp.py /path/to/transcript.json
Appends to _search_batches.jsonl via run_all_keywords.append_batch.
"""
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
from process_run import ALL_KEYWORDS  # noqa: E402
from run_all_keywords import append_batch, strip_job  # noqa: E402


def walk(obj, hits):
    if isinstance(obj, dict):
        if obj.get("status") == "ok" and "jobs" in obj and any(
            j.get("url", "").find("upwork.com/jobs") >= 0 for j in obj.get("jobs", [])[:1]
        ):
            hits.append(obj)
        for v in obj.values():
            walk(v, hits)
    elif isinstance(obj, list):
        for x in obj:
            walk(x, hits)


def main():
    path = Path(sys.argv[1])
    data = json.loads(path.read_text())
    hits = []
    walk(data, hits)
    seen_kw = set()
    for h in hits:
        kw = h.get("_keyword")
        if not kw:
            continue
        if kw in seen_kw:
            continue
        seen_kw.add(kw)
        jobs = [strip_job(j) for j in h.get("jobs", [])]
        append_batch(kw, jobs)
    missing = [k for k in ALL_KEYWORDS if k not in seen_kw]
    for kw in missing:
        append_batch(kw, [], error=True)
    print(json.dumps({"extracted": len(seen_kw), "missing": len(missing)}))


if __name__ == "__main__":
    main()
