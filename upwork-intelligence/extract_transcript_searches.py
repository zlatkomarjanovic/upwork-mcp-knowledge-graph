#!/usr/bin/env python3
"""Extract Upwork find_jobs search results from a cloud agent transcript."""
import json
import sys
from pathlib import Path


def parse_result(val):
    res = val.get("result")
    if isinstance(res, str):
        try:
            res = json.loads(res)
        except json.JSONDecodeError:
            return None, "parse_error"
    if not isinstance(res, dict):
        return None, "invalid"
    if res.get("status") == "ok":
        return res.get("jobs", []), None
    err = res.get("error") or res.get("message") or "error"
    return None, err


def main():
    transcript = Path(sys.argv[1])
    keywords_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).parent / "keywords.json"
    out = Path(sys.argv[3]) if len(sys.argv) > 3 else Path(__file__).parent / "search_responses.json"

    meta = json.loads(keywords_path.read_text())
    data = json.loads(transcript.read_text())

    job_results = []
    for m in data.get("messages", []):
        if m.get("tool_name") != "mcp":
            continue
        tr = m.get("tool_result")
        if not isinstance(tr, dict):
            continue
        val = tr.get("value") or {}
        if val.get("selectedTool") != "upwork__find_jobs":
            continue
        jobs, err = parse_result(val)
        job_results.append({"jobs": jobs, "error": err})

    searches = []
    errors = []
    for i, kwmeta in enumerate(meta):
        kw, grp = kwmeta["keyword"], kwmeta["group"]
        if i < len(job_results):
            r = job_results[i]
            if r.get("error") or r.get("jobs") is None:
                searches.append({"keyword": kw, "group": grp, "error": True})
                errors.append(kw)
            else:
                searches.append({"keyword": kw, "group": grp, "jobs": r["jobs"]})
        else:
            searches.append({"keyword": kw, "group": grp, "error": True})
            errors.append(kw)

    out.write_text(json.dumps({"searches": searches, "errors": errors}, indent=0))
    completed = sum(1 for s in searches if not s.get("error"))
    print(f"extracted {completed}/{len(searches)} keywords from {len(job_results)} mcp results")


if __name__ == "__main__":
    main()
