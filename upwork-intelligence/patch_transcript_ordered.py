#!/usr/bin/env python3
"""Patch search_responses.json using ordered find_jobs results from transcript."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
_KW = json.loads((ROOT / "keywords.json").read_text())
KEYWORDS = [{"keyword": k, "group": g} for k, g in _KW["keywords"].items()]
SEARCH = ROOT / "search_responses.json"


def slim(resp: dict) -> dict:
    jobs = []
    for j in resp.get("jobs") or []:
        jobs.append({k: v for k, v in j.items() if k != "description_snippet"})
    out = {"status": resp.get("status", "ok"), "jobs": jobs}
    for k in ("error_code", "error"):
        if k in resp:
            out[k] = resp[k]
    return out


def collect_results(data: dict) -> list[dict]:
    out = []
    for m in data.get("messages") or []:
        if m.get("role") != "tool" or m.get("tool_name") != "mcp":
            continue
        val = (m.get("tool_result") or {}).get("value") or {}
        if val.get("selectedTool") != "upwork__find_jobs":
            continue
        raw = val.get("result")
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except json.JSONDecodeError:
                raw = {"status": "error", "error_code": "PARSE_ERROR"}
        out.append(slim(raw))
    return out


def main():
    transcript = Path(sys.argv[1])
    data = json.loads(transcript.read_text())
    responses = collect_results(data)
    paired = json.loads(SEARCH.read_text()) if SEARCH.exists() else []
    if not paired:
        paired = [{"keyword": s["keyword"], "group": s["group"], "response": {}} for s in KEYWORDS]
    index = {e["keyword"]: i for i, e in enumerate(paired)}
    for i, spec in enumerate(KEYWORDS):
        if i >= len(responses):
            break
        kw = spec["keyword"]
        entry = {"keyword": kw, "group": spec["group"], "response": responses[i]}
        if kw in index:
            paired[index[kw]] = entry
        else:
            paired.append(entry)
            index[kw] = len(paired) - 1
    SEARCH.write_text(json.dumps(paired, indent=2))
    print(json.dumps({"patched": min(len(responses), len(KEYWORDS)), "total_responses_in_transcript": len(responses)}))


if __name__ == "__main__":
    main()
