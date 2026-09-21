#!/usr/bin/env python3
"""Extract find_jobs MCP results from cloud agent transcript (ordered pairing)."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INDEX = ROOT / "search_index.jsonl"
_KW_FILE = json.loads((ROOT / "keywords.json").read_text())
KEYWORDS = [{"keyword": k, "group": g} for k, g in _KW_FILE["keywords"].items()]


def collect_find_jobs_by_trace(data: dict) -> tuple[dict[str, dict], list[dict]]:
    by_trace: dict[str, dict] = {}
    ordered: list[dict] = []
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
        ordered.append(raw)
        tid = raw.get("trace_id")
        if tid:
            by_trace[tid] = raw
    return by_trace, ordered


def load_index() -> dict[str, str]:
    mapping: dict[str, str] = {}
    if not INDEX.exists():
        return mapping
    for line in INDEX.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        mapping[row["keyword"]] = row["trace_id"]
    return mapping


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: extract_transcript_searches.py <transcript.json>", file=sys.stderr)
        sys.exit(1)
    transcript_path = Path(sys.argv[1])
    data = json.loads(transcript_path.read_text())
    by_trace, ordered = collect_find_jobs_by_trace(data)
    kw_to_trace = load_index()

    paired = []
    order_i = 0
    for spec in KEYWORDS:
        kw = spec["keyword"]
        resp = None
        tid = kw_to_trace.get(kw)
        if tid and tid in by_trace:
            resp = by_trace[tid]
        elif order_i < len(ordered):
            resp = ordered[order_i]
            order_i += 1
        else:
            resp = {"status": "error", "error_code": "MISSING_SEARCH"}
        paired.append({"keyword": kw, "group": spec["group"], "response": resp})

    out = ROOT / "search_responses.json"
    existing = {}
    if out.exists():
        for e in json.loads(out.read_text()):
            existing[e["keyword"]] = e
    for p in paired:
        if p["response"].get("status") == "ok" or p["response"].get("jobs") is not None:
            existing[p["keyword"]] = p
        elif p["keyword"] not in existing:
            existing[p["keyword"]] = p
    merged = [existing[k] for k in _KW_FILE["keywords"] if k in existing]
    out.write_text(json.dumps(merged, indent=2))
    ok = sum(1 for p in merged if p["response"].get("status") == "ok")
    missing = [p["keyword"] for p in merged if p["response"].get("error_code") == "MISSING_SEARCH"]
    print(
        f"Paired {len(merged)} keywords from {len(ordered)} transcript searches; "
        f"index={len(kw_to_trace)}; ok={ok}; missing={len(missing)}"
    )


if __name__ == "__main__":
    main()
