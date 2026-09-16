#!/usr/bin/env python3
"""Convert raw_search_results.json to _search_batches.jsonl for process_run.py."""
import json
from pathlib import Path

BASE = Path(__file__).parent
RAW = BASE / "raw_search_results.json"
BATCH = BASE / "_search_batches.jsonl"


def slim_job(j):
    return {k: j[k] for k in j if k != "description_snippet"}


def main():
    lines = []
    if RAW.exists():
        data = json.loads(RAW.read_text())
        for s in data.get("searches", []):
            resp = s.get("response") or {}
            jobs = [slim_job(j) for j in resp.get("jobs") or []]
            lines.append(json.dumps({"keyword": s["keyword"], "jobs": jobs}, ensure_ascii=False))
        for kw in data.get("errors", []):
            lines.append(json.dumps({"keyword": kw, "error": True}, ensure_ascii=False))
    BATCH.write_text("\n".join(lines) + ("\n" if lines else ""))
    print(json.dumps({"lines": len(lines)}))


if __name__ == "__main__":
    main()
