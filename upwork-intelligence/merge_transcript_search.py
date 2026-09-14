#!/usr/bin/env python3
"""Merge last-N transcript find_jobs into search_responses.json (fill gaps from prior file)."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent
SEARCH = ROOT / "search_responses.json"
_KEYW = json.loads((ROOT / "keywords.json").read_text())
KEYWORDS = [{"keyword": k, "group": g} for k, g in _KEYW["keywords"].items()]


def slim(resp: dict) -> dict:
    jobs = []
    for j in resp.get("jobs") or []:
        jobs.append({k: v for k, v in j.items() if k != "description_snippet"})
    out = {"status": resp.get("status", "ok"), "jobs": jobs}
    for k in ("error_code", "error"):
        if k in resp:
            out[k] = resp[k]
    return out


def collect_find_jobs(data: dict) -> list[dict]:
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
        results.append(raw)
    return results


def main() -> None:
    transcript = Path(sys.argv[1])
    data = json.loads(transcript.read_text())
    responses = collect_find_jobs(data)
    n = len(KEYWORDS)
    offset = int(sys.argv[2]) if len(sys.argv) > 2 else max(0, len(responses) - n)
    if offset > 0 and len(responses) >= offset + n:
        responses = responses[offset : offset + n]
    elif len(responses) >= n:
        responses = responses[-n:]
    prior = {}
    if SEARCH.exists():
        for e in json.loads(SEARCH.read_text()):
            prior[e["keyword"]] = e.get("response") or {}

    paired = []
    errors = []
    for i, spec in enumerate(KEYWORDS):
        kw = spec["keyword"]
        resp = responses[i] if i < len(responses) else None
        if not resp or resp.get("status") == "error" or resp.get("error_code"):
            if kw in prior and prior[kw].get("status") == "ok":
                resp = prior[kw]
            else:
                resp = resp or {"status": "error", "error_code": "MISSING_SEARCH"}
                errors.append(kw)
        paired.append({"keyword": kw, "group": spec["group"], "response": slim(resp)})

    SEARCH.write_text(json.dumps(paired, indent=2))
    ok = sum(1 for p in paired if p["response"].get("status") == "ok")
    print(json.dumps({"keywords": len(paired), "ok": ok, "errors": errors, "transcript_searches": len(collect_find_jobs(data))}))


if __name__ == "__main__":
    main()
