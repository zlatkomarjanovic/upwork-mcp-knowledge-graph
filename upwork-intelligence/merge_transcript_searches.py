#!/usr/bin/env python3
"""Merge find_jobs results from cloud agent transcript into search_responses.json by call order."""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SEARCH = ROOT / "search_responses.json"
_KW = json.loads((ROOT / "keywords.json").read_text())
KEYWORDS = [{"keyword": k, "group": g} for k, g in _KW["keywords"].items()]


def slim(resp: dict) -> dict:
    out = {k: v for k, v in resp.items() if k not in ("client_rating_basis", "description_snippet")}
    jobs = []
    for j in out.get("jobs") or []:
        jobs.append({k: v for k, v in j.items() if k != "description_snippet"})
    out["jobs"] = jobs
    return out


def collect_find_jobs_results(data: dict) -> list[dict]:
    results = []
    for m in data.get("messages") or []:
        if m.get("role") != "tool" or m.get("tool_name") != "mcp":
            continue
        value = (m.get("tool_result") or {}).get("value") or {}
        if value.get("selectedTool") != "upwork__find_jobs":
            continue
        raw = value.get("result")
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except json.JSONDecodeError:
                raw = {"status": "error", "error_code": "PARSE_ERROR"}
        results.append(slim(raw))
    return results


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: merge_transcript_searches.py <transcript.json>", file=sys.stderr)
        sys.exit(1)
    transcript_path = Path(sys.argv[1])
    data = json.loads(transcript_path.read_text())
    responses = collect_find_jobs_results(data)

    paired = json.loads(SEARCH.read_text()) if SEARCH.exists() else []
    index = {e["keyword"]: i for i, e in enumerate(paired)}
    if not paired:
        for spec in KEYWORDS:
            paired.append({"keyword": spec["keyword"], "group": spec["group"], "response": {"status": "ok", "jobs": []}})
            index[spec["keyword"]] = len(paired) - 1

    start = int(os.environ.get("MERGE_START_INDEX", "0"))
    offset = int(os.environ.get("MERGE_OFFSET", "0"))
    updated = 0
    for i, resp in enumerate(responses):
        if i < start:
            continue
        ki = i - offset
        if ki < 0 or ki >= len(KEYWORDS):
            continue
        kw = KEYWORDS[ki]["keyword"]
        group = KEYWORDS[ki]["group"]
        entry = {"keyword": kw, "group": group, "response": resp}
        if kw in index:
            paired[index[kw]] = entry
        else:
            paired.append(entry)
            index[kw] = len(paired) - 1
        updated += 1

    SEARCH.write_text(json.dumps(paired, indent=2))
    missing = max(0, len(KEYWORDS) - len(responses))
    print(json.dumps({"transcript_searches": len(responses), "merged": updated, "keywords_missing": missing}))


if __name__ == "__main__":
    main()
