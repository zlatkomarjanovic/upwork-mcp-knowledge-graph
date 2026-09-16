#!/usr/bin/env python3
"""Pair transcript find_jobs results with keywords.json order (search batch order)."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
KW_DATA = json.loads((ROOT / "keywords.json").read_text())
KEYWORDS = [{"keyword": k, "group": g} for k, g in KW_DATA["keywords"].items()]


def collect_results(data: dict) -> list[dict]:
    out = []
    for m in data.get("messages") or []:
        if m.get("role") != "tool":
            continue
        val = (m.get("tool_result") or {}).get("value")
        if not isinstance(val, dict) or val.get("selectedTool") != "upwork__find_jobs":
            continue
        raw = val.get("result")
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except json.JSONDecodeError:
                raw = {"status": "error", "error_code": "PARSE_ERROR"}
        out.append(raw)
    return out


def main() -> None:
    path = Path(sys.argv[1])
    data = json.loads(path.read_text())
    results = collect_results(data)
    paired = []
    for i, spec in enumerate(KEYWORDS):
        if i < len(results):
            resp = results[i]
        else:
            resp = {"status": "error", "error_code": "MISSING_SEARCH"}
        paired.append({"keyword": spec["keyword"], "group": spec["group"], "response": resp})
    out = ROOT / "search_responses.json"
    out.write_text(json.dumps(paired, indent=2))
    ok = sum(1 for p in paired if p["response"].get("status") == "ok")
    missing = [p["keyword"] for p in paired if p["response"].get("error_code") == "MISSING_SEARCH"]
    print(json.dumps({"searches_in_transcript": len(results), "ok": ok, "missing": len(missing), "missing_keywords": missing}))


if __name__ == "__main__":
    main()
