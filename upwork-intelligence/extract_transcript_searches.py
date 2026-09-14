#!/usr/bin/env python3
"""Extract find_jobs MCP results from cloud agent transcript (ordered pairing)."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
_KW_FILE = json.loads((ROOT / "keywords.json").read_text())
KEYWORDS = [{"keyword": k, "group": g} for k, g in _KW_FILE["keywords"].items()]


def _mcp_value(message: dict) -> dict:
    tr = message.get("tool_result") or {}
    if tr.get("resultType") == "mcpResult":
        return tr.get("value") or {}
    return tr.get("value") or {}


def collect_find_jobs_results(data: dict) -> list[dict]:
    results: list[dict] = []
    for m in data.get("messages") or []:
        if m.get("role") != "tool" or m.get("tool_name") != "mcp":
            continue
        value = _mcp_value(m)
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


def collect_find_jobs_by_keyword(data: dict) -> dict[str, dict]:
    """Pair transcript searches with keywords.json order (one search per keyword in run order)."""
    results = collect_find_jobs_results(data)
    by_kw: dict[str, dict] = {}
    for i, spec in enumerate(KEYWORDS):
        if i < len(results):
            by_kw[spec["keyword"]] = results[i]
    return by_kw


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: extract_transcript_searches.py <transcript.json>", file=sys.stderr)
        sys.exit(1)
    transcript_path = Path(sys.argv[1])
    data = json.loads(transcript_path.read_text())
    by_kw = collect_find_jobs_by_keyword(data)

    paired = []
    for spec in KEYWORDS:
        kw = spec["keyword"]
        if kw in by_kw:
            resp = by_kw[kw]
        else:
            resp = {"status": "error", "error_code": "MISSING_SEARCH"}
        paired.append({"keyword": kw, "group": spec["group"], "response": resp})

    out = ROOT / "search_responses.json"
    out.write_text(json.dumps(paired, indent=2))
    ok = sum(1 for p in paired if p.get("response", {}).get("status") == "ok")
    missing = [p["keyword"] for p in paired if p["response"].get("error_code") == "MISSING_SEARCH"]
    print(f"Paired {len(paired)} keywords from {len(by_kw)} transcript searches; ok={ok}; missing={len(missing)}")


if __name__ == "__main__":
    main()
