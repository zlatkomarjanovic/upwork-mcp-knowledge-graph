#!/usr/bin/env python3
"""Pair find_jobs MCP results with keywords by query param from tool call."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
KEYWORDS = json.loads((ROOT / "keywords.json").read_text())
KW_BY_LOWER = {k["keyword"].lower(): k for k in KEYWORDS}


def parse_result(raw):
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"status": "error", "error_code": "PARSE_ERROR"}
    return raw or {"status": "error", "error_code": "MISSING_SEARCH"}


def extract_query_from_call(msg: dict) -> str | None:
    # Tool call args may live in several shapes depending on transcript version.
    for key in ("arguments", "input", "tool_input"):
        val = msg.get(key)
        if isinstance(val, str):
            try:
                val = json.loads(val)
            except json.JSONDecodeError:
                continue
        if isinstance(val, dict):
            params = val.get("params") or {}
            if params.get("query"):
                return str(params["query"]).strip()
            if val.get("query"):
                return str(val["query"]).strip()
    return None


def collect_pairs(data: dict) -> dict[str, dict]:
    """keyword -> response (last wins for duplicate queries)."""
    by_kw: dict[str, dict] = {}
    pending_query: str | None = None
    messages = data.get("messages") or []

    for m in messages:
        role = m.get("role")
        if role == "assistant":
            for tc in m.get("tool_calls") or []:
                if tc.get("tool_name") == "mcp" or tc.get("name") == "upwork__find_jobs":
                    q = extract_query_from_call(tc)
                    if q:
                        pending_query = q
                elif "find_jobs" in str(tc.get("tool_name", "")):
                    q = extract_query_from_call(tc)
                    if q:
                        pending_query = q
        if role == "tool" and m.get("tool_name") == "mcp":
            value = (m.get("tool_result") or {}).get("value") or {}
            if value.get("selectedTool") != "upwork__find_jobs":
                continue
            resp = parse_result(value.get("result"))
            q = pending_query
            pending_query = None
            if q:
                by_kw[q.lower()] = resp
    return by_kw


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: extract_transcript_by_query.py <transcript.json>", file=sys.stderr)
        sys.exit(1)
    transcript_path = Path(sys.argv[1])
    data = json.loads(transcript_path.read_text())
    by_kw = collect_pairs(data)

    paired = []
    missing = []
    for spec in KEYWORDS:
        kw = spec["keyword"]
        resp = by_kw.get(kw.lower())
        if not resp:
            missing.append(kw)
            resp = {"status": "error", "error_code": "MISSING_SEARCH"}
        paired.append({"keyword": kw, "group": spec["group"], "response": resp})

    out = ROOT / "search_responses.json"
    out.write_text(json.dumps(paired, indent=2))
    ok = sum(1 for p in paired if p["response"].get("status") == "ok")
    print(f"Mapped {len(by_kw)} transcript searches; paired ok={ok}/93; missing={len(missing)}")
    if missing:
        print("Missing:", ", ".join(missing[:20]), ("..." if len(missing) > 20 else ""))


if __name__ == "__main__":
    main()
