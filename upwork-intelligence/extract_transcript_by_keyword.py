#!/usr/bin/env python3
"""Pair find_jobs MCP results from transcript by search query keyword."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
_KW = json.loads((ROOT / "keywords.json").read_text())
GROUPS = _KW["keywords"]


def slim(resp: dict) -> dict:
    jobs = []
    for j in resp.get("jobs") or []:
        jobs.append({k: v for k, v in j.items() if k != "description_snippet"})
    out = {"status": resp.get("status", "ok"), "jobs": jobs}
    for k in ("error_code", "error", "hasMore", "next_cursor", "pageInfo", "client_rating_basis", "trace_id"):
        if k in resp:
            out[k] = resp[k]
    return out


def extract_pairs(data: dict) -> dict[str, dict]:
    by_kw: dict[str, dict] = {}
    for m in data.get("messages") or []:
        if m.get("role") != "tool" or m.get("tool_name") != "mcp":
            continue
        value = (m.get("tool_result") or {}).get("value") or {}
        if value.get("selectedTool") != "upwork__find_jobs":
            continue
        args = value.get("arguments") or {}
        params = (args.get("params") or {}) if isinstance(args, dict) else {}
        kw = params.get("query") or params.get("title")
        if not kw:
            continue
        raw = value.get("result")
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except json.JSONDecodeError:
                raw = {"status": "error", "error_code": "PARSE_ERROR"}
        by_kw[kw] = slim(raw)
    return by_kw


def main() -> None:
    path = Path(sys.argv[1])
    data = json.loads(path.read_text())
    by_kw = extract_pairs(data)
    paired = []
    errors = []
    for kw, group in GROUPS.items():
        resp = by_kw.get(kw)
        if resp is None:
            errors.append(kw)
            resp = {"status": "error", "error_code": "MISSING_SEARCH"}
        paired.append({"keyword": kw, "group": group, "response": resp})
    (ROOT / "search_responses.json").write_text(json.dumps(paired, indent=2))
    ok = sum(1 for p in paired if p["response"].get("status") == "ok")
    print(json.dumps({"ok": ok, "missing": len(errors), "found_in_transcript": len(by_kw)}))


if __name__ == "__main__":
    main()
