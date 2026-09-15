#!/usr/bin/env python3
"""Build search_responses.json from agent transcript find_jobs calls."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
KW_FILE = json.loads((ROOT / "keywords.json").read_text())
GROUPS = KW_FILE["keywords"]
ORDER = list(GROUPS.keys())


def slim(resp: dict) -> dict:
    jobs = []
    for j in resp.get("jobs") or []:
        jobs.append({k: v for k, v in j.items() if k != "description_snippet"})
    out = {"status": resp.get("status", "ok"), "jobs": jobs}
    for k in ("error_code", "error"):
        if k in resp:
            out[k] = resp[k]
    return out


def _parse_find_jobs_result(value: dict) -> dict:
    raw = value.get("result")
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError:
            raw = {"status": "error", "error_code": "PARSE_ERROR"}
    if not isinstance(raw, dict):
        return {"status": "error", "error_code": "PARSE_ERROR"}
    if raw.get("status") == "error" or raw.get("error_code"):
        return slim(raw)
    return slim(raw)


def extract_from_transcript(data: dict) -> dict[str, dict]:
    """Map keyword -> response using find_jobs tool results in transcript order."""
    results: list[dict] = []
    for m in data.get("messages") or []:
        if m.get("role") != "tool" or m.get("tool_name") != "mcp":
            continue
        value = (m.get("tool_result") or {}).get("value") or {}
        if value.get("selectedTool") != "upwork__find_jobs":
            continue
        results.append(_parse_find_jobs_result(value))

    by_kw: dict[str, dict] = {}
    for i, kw in enumerate(ORDER):
        if i < len(results):
            by_kw[kw] = results[i]
    return by_kw


def main() -> None:
    transcript_path = Path(sys.argv[1])
    data = json.loads(transcript_path.read_text())
    by_kw = extract_from_transcript(data)
    paired = []
    missing = []
    for kw in ORDER:
        resp = by_kw.get(kw)
        if not resp:
            missing.append(kw)
            resp = {"status": "error", "error_code": "MISSING_SEARCH", "jobs": []}
        paired.append({"keyword": kw, "group": GROUPS[kw], "response": resp})
    (ROOT / "search_responses.json").write_text(json.dumps(paired, indent=2))
    ok = sum(1 for p in paired if p["response"].get("status") == "ok")
    print(json.dumps({"keywords": len(paired), "ok": ok, "missing": len(missing)}, indent=2))


if __name__ == "__main__":
    main()
