#!/usr/bin/env python3
"""Merge ordered transcript find_jobs results with prior search_responses fallback."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent
_kw = json.loads((ROOT / "keywords.json").read_text())
KEYWORDS = list(_kw["keywords"].keys())
SEARCH = ROOT / "search_responses.json"
GROUPS = _kw["keywords"]


def parse_result(raw):
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"status": "error", "error_code": "PARSE_ERROR"}
    return raw if isinstance(raw, dict) else {"status": "error", "error_code": "INVALID"}


def slim_job(j: dict) -> dict:
    return {k: v for k, v in j.items() if k != "description_snippet"}


def collect_ordered_results(transcript: dict) -> list[dict]:
    out = []
    for m in transcript.get("messages") or []:
        if m.get("role") != "tool" or m.get("tool_name") != "mcp":
            continue
        val = (m.get("tool_result") or {}).get("value") or {}
        if val.get("selectedTool") != "upwork__find_jobs":
            continue
        resp = parse_result(val.get("result"))
        if resp.get("jobs"):
            resp = dict(resp)
            resp["jobs"] = [slim_job(j) for j in resp["jobs"]]
        out.append(resp)
    return out


def main():
    if len(sys.argv) < 2:
        print("Usage: merge_transcript_and_snapshot.py <transcript.json> [keyword_order.json]", file=sys.stderr)
        sys.exit(1)
    transcript = json.loads(Path(sys.argv[1]).read_text())
    live = collect_ordered_results(transcript)
    order = KEYWORDS
    if len(sys.argv) >= 3:
        order = json.loads(Path(sys.argv[2]).read_text())
    # Use the most recent keyword pass when the transcript contains extra searches.
    if len(live) >= len(order):
        live = live[-len(order) :]
    fallback = {}
    if SEARCH.exists():
        for e in json.loads(SEARCH.read_text()):
            fallback[e["keyword"]] = e.get("response") or {}
    paired = []
    for i, kw in enumerate(order):
        if i < len(live) and live[i].get("status") == "ok":
            resp = live[i]
        elif kw in fallback:
            resp = fallback[kw]
        else:
            resp = {"status": "error", "error_code": "MISSING_SEARCH"}
        paired.append({"keyword": kw, "group": GROUPS[kw], "response": resp})
    SEARCH.write_text(json.dumps(paired, indent=2))
    ok = sum(1 for p in paired if p["response"].get("status") == "ok")
    print(json.dumps({"live_results": len(live), "paired_ok": ok, "keywords": len(paired)}))


if __name__ == "__main__":
    main()
