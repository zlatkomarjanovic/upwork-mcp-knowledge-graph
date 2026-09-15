#!/usr/bin/env python3
"""Rebuild search_responses.json from transcript find_jobs calls (match by query)."""
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


def parse_result(raw) -> dict:
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"status": "error", "error_code": "PARSE_ERROR"}
    return raw if isinstance(raw, dict) else {"status": "error", "error_code": "INVALID"}


def collect_by_keyword(data: dict) -> dict[str, dict]:
    by_kw: dict[str, dict] = {}
    messages = data.get("messages") or []
    for i, m in enumerate(messages):
        if m.get("role") != "assistant":
            continue
        tool_calls = m.get("tool_calls") or []
        for tc in tool_calls:
            if tc.get("tool_name") != "mcp":
                continue
            args_raw = tc.get("arguments") or tc.get("args") or {}
            if isinstance(args_raw, str):
                try:
                    args_raw = json.loads(args_raw)
                except json.JSONDecodeError:
                    continue
            sel = args_raw.get("selectedTool") or args_raw.get("toolName")
            if sel != "upwork__find_jobs":
                continue
            inner = args_raw.get("arguments") or args_raw
            if inner.get("action") != "search":
                continue
            params = inner.get("params") or {}
            query = (params.get("query") or params.get("title") or "").strip()
            if not query:
                continue
            # find matching tool result in following messages
            tc_id = tc.get("id") or tc.get("tool_call_id")
            resp = None
            for j in range(i + 1, min(i + 8, len(messages))):
                tm = messages[j]
                if tm.get("role") != "tool":
                    continue
                tr = tm.get("tool_result") or {}
                if tc_id and tr.get("tool_call_id") not in (None, tc_id):
                    continue
                val = tr.get("value") or {}
                if val.get("selectedTool") == "upwork__find_jobs" or tr.get("tool_name") == "mcp":
                    raw = val.get("result") if val else tr.get("content")
                    if raw is not None:
                        resp = parse_result(raw)
                        break
            if resp is None:
                continue
            # keep latest search per keyword (hourly re-run overwrites)
            by_kw[query] = slim(resp)
            # alias: case-insensitive match to configured keywords
            for spec in KEYWORDS:
                if spec["keyword"].lower() == query.lower():
                    by_kw[spec["keyword"]] = slim(resp)
    return by_kw


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: extract_transcript_by_keyword.py <transcript.json>", file=sys.stderr)
        sys.exit(1)
    data = json.loads(Path(sys.argv[1]).read_text())
    by_kw = collect_by_keyword(data)
    existing_map = {}
    if SEARCH.exists():
        for e in json.loads(SEARCH.read_text()):
            existing_map[e["keyword"]] = e.get("response") or {}
    paired = []
    missing = []
    for spec in KEYWORDS:
        kw = spec["keyword"]
        resp = by_kw.get(kw)
        if not resp:
            prev = existing_map.get(kw) or {}
            if prev.get("status") == "ok" and prev.get("jobs") is not None:
                resp = prev
            else:
                missing.append(kw)
                resp = {"status": "error", "error_code": "MISSING_SEARCH"}
        paired.append({"keyword": kw, "group": spec["group"], "response": resp})
    SEARCH.write_text(json.dumps(paired, indent=2))
    ok = sum(1 for p in paired if p["response"].get("status") == "ok")
    print(f"keywords={len(paired)} ok={ok} missing={len(missing)}")
    if missing:
        print("missing:", ", ".join(missing[:20]), ("..." if len(missing) > 20 else ""))


if __name__ == "__main__":
    main()
