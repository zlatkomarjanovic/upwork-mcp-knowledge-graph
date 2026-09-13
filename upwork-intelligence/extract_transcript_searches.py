#!/usr/bin/env python3
"""Extract find_jobs MCP results from cloud agent transcript."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
_KEYWORD_FILE = json.loads((ROOT / "keywords.json").read_text())
KEYWORDS = [{"keyword": k, "group": g} for k, g in _KEYWORD_FILE["keywords"].items()]


def keyword_from_tool_call(message: dict) -> str | None:
    """Best-effort keyword from MCP tool call arguments."""
    for block in message.get("content") or []:
        if block.get("type") != "tool_use":
            continue
        if block.get("name") not in ("mcp", "CallDynamicTool", "upwork__find_jobs"):
            continue
        inp = block.get("input") or block.get("arguments") or {}
        if isinstance(inp, str):
            try:
                inp = json.loads(inp)
            except json.JSONDecodeError:
                continue
        params = (inp.get("arguments") or inp).get("params") or inp.get("params") or {}
        q = params.get("query") or params.get("title")
        if q:
            return q.strip()
    return None


def collect_find_jobs_by_keyword(data: dict) -> dict[str, dict]:
    by_kw: dict[str, dict] = {}
    ordered: list[dict] = []
    messages = data.get("messages") or []
    i = 0
    while i < len(messages):
        m = messages[i]
        if m.get("role") == "assistant":
            kw = keyword_from_tool_call(m)
            if kw and i + 1 < len(messages):
                nxt = messages[i + 1]
                if nxt.get("role") == "tool" and nxt.get("tool_name") == "mcp":
                    value = (nxt.get("tool_result") or {}).get("value") or {}
                    if value.get("selectedTool") == "upwork__find_jobs":
                        raw = value.get("result")
                        if isinstance(raw, str):
                            try:
                                raw = json.loads(raw)
                            except json.JSONDecodeError:
                                raw = {"status": "error", "error_code": "PARSE_ERROR"}
                        if kw not in by_kw:
                            by_kw[kw] = raw
                        ordered.append(raw)
        if m.get("role") == "tool" and m.get("tool_name") == "mcp":
            value = (m.get("tool_result") or {}).get("value") or {}
            if value.get("selectedTool") == "upwork__find_jobs":
                raw = value.get("result")
                if isinstance(raw, str):
                    try:
                        raw = json.loads(raw)
                    except json.JSONDecodeError:
                        raw = {"status": "error", "error_code": "PARSE_ERROR"}
                ordered.append(raw)
        i += 1
    by_kw["_ordered"] = ordered  # type: ignore[assignment]
    return by_kw


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: extract_transcript_searches.py <transcript.json>", file=sys.stderr)
        sys.exit(1)
    transcript_path = Path(sys.argv[1])
    data = json.loads(transcript_path.read_text())
    collected = collect_find_jobs_by_keyword(data)
    ordered = collected.pop("_ordered", [])

    paired = []
    missing = []
    for spec in KEYWORDS:
        kw = spec["keyword"]
        resp = collected.get(kw)
        if resp is None and ordered:
            # fallback: positional for legacy transcripts
            idx = len(paired)
            resp = ordered[idx] if idx < len(ordered) else None
        if resp is None:
            resp = {"status": "error", "error_code": "MISSING_SEARCH"}
            missing.append(kw)
        paired.append({"keyword": kw, "group": spec["group"], "response": resp})

    out = ROOT / "search_responses.json"
    out.write_text(json.dumps(paired, indent=2))
    ok = sum(1 for p in paired if p["response"].get("status") == "ok")
    print(
        json.dumps(
            {
                "paired": len(paired),
                "ok": ok,
                "missing": len(missing),
                "transcript_searches": len(ordered),
                "mapped_by_query": len(collected),
            }
        )
    )


if __name__ == "__main__":
    main()
