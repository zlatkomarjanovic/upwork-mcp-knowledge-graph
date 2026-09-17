#!/usr/bin/env python3
"""Pair find_jobs MCP call arguments with results from transcript."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent
GROUPS = json.loads((ROOT / "keywords.json").read_text())["keywords"]
SEARCH = ROOT / "search_responses.json"


def slim(resp: dict) -> dict:
    jobs = [{k: v for k, v in j.items() if k != "description_snippet"} for j in resp.get("jobs") or []]
    out = {"status": resp.get("status", "ok"), "jobs": jobs}
    if resp.get("error_code"):
        out["status"] = "error"
        out["error_code"] = resp["error_code"]
    return out


def main() -> None:
    data = json.loads(Path(sys.argv[1]).read_text())
    msgs = data.get("messages") or []
    pending_kw: list[str | None] = []
    by_kw: dict[str, dict] = {}

    i = 0
    while i < len(msgs):
        m = msgs[i]
        if m.get("role") == "assistant":
            for tc in m.get("tool_calls") or []:
                if tc.get("tool_name") != "mcp":
                    continue
                # next messages may include tool result; args often in separate structure
                pending_kw.append(None)
        if m.get("role") == "tool" and m.get("tool_name") == "mcp":
            val = (m.get("tool_result") or {}).get("value") or {}
            if val.get("selectedTool") != "upwork__find_jobs":
                i += 1
                continue
            raw = val.get("result")
            if isinstance(raw, str):
                try:
                    raw = json.loads(raw)
                except json.JSONDecodeError:
                    raw = {"status": "error", "error_code": "PARSE_ERROR"}
            # skip bridge failures
            if raw.get("error_code") == "HTTP_401":
                i += 1
                continue
            i += 1
            continue
        i += 1

    # Second pass: find assistant messages with mcpDetails in transcript - not available

    # Pair by order: collect successful find_jobs only
    responses: list[dict] = []
    for m in msgs:
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
                continue
        if raw.get("error_code") in ("HTTP_401", "SENSITIVE_RATE_LIMIT_EXCEEDED"):
            continue
        if raw.get("status") == "ok" or raw.get("jobs"):
            responses.append(slim(raw))

    # Pair with keyword order from first N keywords attempted in session (by call order in assistant steps)
    call_keywords: list[str] = []
    for m in msgs:
        if m.get("role") != "assistant":
            continue
        text = json.dumps(m)
        if "upwork__find_jobs" not in text and '"query"' not in text:
            continue
        # look for tool call payload in message if present
        for block in m.get("content") or []:
            if isinstance(block, dict) and block.get("type") == "text":
                t = block.get("text") or ""
                if '"query"' in t:
                    try:
                        obj = json.loads(t)
                        q = (obj.get("arguments") or {}).get("params", {}).get("query")
                        if q:
                            call_keywords.append(q)
                    except json.JSONDecodeError:
                        pass

    # Fallback: use ordered responses count vs keywords - match by index from transcript tool call steps
    # Build keyword list from grep of user-visible tool invocations in transcript raw file
    import re

    raw_text = Path(sys.argv[1]).read_text()
    found = re.findall(r'"query":\s*"([^"]+)"', raw_text)
    # dedupe consecutive same
    ordered_kw: list[str] = []
    for q in found:
        if not ordered_kw or ordered_kw[-1] != q:
            ordered_kw.append(q)

    ok_responses = responses
    for idx, kw in enumerate(ordered_kw):
        if idx >= len(ok_responses):
            break
        if kw in GROUPS:
            by_kw[kw] = ok_responses[idx]

    backup = json.loads(Path(sys.argv[2]).read_text()) if len(sys.argv) > 2 else []
    backup_map = {e["keyword"]: e for e in backup}
    paired = []
    for kw in GROUPS:
        if kw in by_kw:
            paired.append({"keyword": kw, "group": GROUPS[kw], "response": by_kw[kw]})
        elif kw in backup_map:
            paired.append(backup_map[kw])
        else:
            paired.append({"keyword": kw, "group": GROUPS[kw], "response": {"status": "error", "error_code": "MISSING_SEARCH", "jobs": []}})
    SEARCH.write_text(json.dumps(paired, indent=2))
    print(json.dumps({"live_keywords": len(by_kw), "responses_ok": len(ok_responses), "queries_in_transcript": len(ordered_kw)}))


if __name__ == "__main__":
    main()
