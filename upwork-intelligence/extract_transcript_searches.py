#!/usr/bin/env python3
"""Extract find_jobs MCP results from cloud agent transcript (ordered pairing)."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
_KW = json.loads((ROOT / "keywords.json").read_text())
KEYWORDS = [{"keyword": k, "group": g} for k, g in _KW["keywords"].items()]


def collect_find_jobs_results(data: dict) -> list[dict]:
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
    if len(sys.argv) < 2:
        print("Usage: extract_transcript_searches.py <transcript.json>", file=sys.stderr)
        sys.exit(1)
    transcript_path = Path(sys.argv[1])
    data = json.loads(transcript_path.read_text())
    responses = collect_find_jobs_results(data)
    # Use the most recent N searches (hourly re-runs append duplicates at end).
    n = len(KEYWORDS)
    if len(responses) >= n:
        responses = responses[-n:]
    elif len(responses) > 0:
        responses = responses + [{"status": "error", "error_code": "MISSING_SEARCH"}] * (n - len(responses))

    paired = []
    for i, spec in enumerate(KEYWORDS):
        resp = responses[i] if i < len(responses) else {"status": "error", "error_code": "MISSING_SEARCH"}
        paired.append({"keyword": spec["keyword"], "group": spec["group"], "response": resp})

    out = ROOT / "search_responses.json"
    out.write_text(json.dumps(paired, indent=2))
    ok = sum(1 for p in paired if p["response"].get("status") == "ok")
    missing = [p["keyword"] for p in paired if p["response"].get("error_code") == "MISSING_SEARCH"]
    print(f"Paired {len(paired)} keywords from {len(responses)} transcript searches; ok={ok}; missing={len(missing)}")


if __name__ == "__main__":
    main()
