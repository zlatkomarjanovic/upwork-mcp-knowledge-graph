#!/usr/bin/env python3
"""Extract find_jobs MCP results from cloud agent transcript (pair by query when available)."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
_kw_file = json.loads((ROOT / "keywords.json").read_text())
KEYWORDS = [{"keyword": k, "group": g} for k, g in _kw_file["keywords"].items()]
KW_SET = {k for k in _kw_file["keywords"]}


def parse_result(raw):
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"status": "error", "error_code": "PARSE_ERROR"}
    return raw if isinstance(raw, dict) else {"status": "error", "error_code": "INVALID_RESULT"}


def extract_query_from_message(m: dict) -> str | None:
    """Best-effort query from assistant tool call payload."""
    for key in ("arguments", "tool_arguments", "input"):
        val = m.get(key)
        if isinstance(val, str):
            try:
                val = json.loads(val)
            except json.JSONDecodeError:
                continue
        if isinstance(val, dict):
            params = val.get("params") or val
            q = params.get("query")
            if q and q in KW_SET:
                return q
    tc = m.get("tool_calls") or []
    for call in tc:
        for key in ("arguments", "input"):
            val = call.get(key)
            if isinstance(val, str):
                try:
                    val = json.loads(val)
                except json.JSONDecodeError:
                    continue
            if isinstance(val, dict):
                params = val.get("params") or val
                q = params.get("query")
                if q and q in KW_SET:
                    return q
    return None


def collect_find_jobs_pairs(data: dict) -> dict[str, dict]:
    """Map keyword -> latest response (by query if known, else ordered fallback)."""
    by_query: dict[str, dict] = {}
    ordered: list[dict] = []
    messages = data.get("messages") or []
    pending_query: str | None = None
    i = 0
    while i < len(messages):
        m = messages[i]
        if m.get("role") == "assistant":
            q = extract_query_from_message(m)
            if q:
                pending_query = q
        if m.get("role") == "tool" and m.get("tool_name") == "mcp":
            value = (m.get("tool_result") or {}).get("value") or {}
            if value.get("selectedTool") != "upwork__find_jobs":
                i += 1
                continue
            resp = parse_result(value.get("result"))
            if pending_query:
                by_query[pending_query] = resp
                pending_query = None
            else:
                ordered.append(resp)
        i += 1
    if not by_query and ordered:
        for idx, spec in enumerate(KEYWORDS):
            if idx < len(ordered):
                by_query[spec["keyword"]] = ordered[idx]
    return by_query


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: extract_transcript_searches.py <transcript.json>", file=sys.stderr)
        sys.exit(1)
    transcript_path = Path(sys.argv[1])
    data = json.loads(transcript_path.read_text())
    by_query = collect_find_jobs_pairs(data)

    paired = []
    missing = []
    for spec in KEYWORDS:
        kw = spec["keyword"]
        if kw in by_query:
            resp = by_query[kw]
        else:
            resp = {"status": "error", "error_code": "MISSING_SEARCH"}
            missing.append(kw)
        paired.append({"keyword": kw, "group": spec["group"], "response": resp})

    out = ROOT / "search_responses.json"
    out.write_text(json.dumps(paired, indent=2))
    ok = sum(1 for p in paired if p["response"].get("status") == "ok")
    print(
        f"Paired {len(paired)} keywords; mapped={len(by_query)}; ok={ok}; missing={len(missing)}"
    )


if __name__ == "__main__":
    main()
