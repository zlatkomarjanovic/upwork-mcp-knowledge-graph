#!/usr/bin/env python3
"""Extract find_jobs MCP results from cloud agent transcript (ordered pairing)."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
KEYWORDS = json.loads((ROOT / "keywords.json").read_text())


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


def to_raw_jsonl(paired: list) -> None:
    raw = ROOT / "raw-search-batch.jsonl"
    with raw.open("a") as f:
        for item in paired:
            kw = item["keyword"]
            resp = item.get("response") or item
            if resp.get("status") == "error" or resp.get("error_code"):
                line = {
                    "keyword": kw,
                    "jobs": [],
                    "error": resp.get("reason") or resp.get("error_code"),
                }
            else:
                line = {"keyword": kw, "jobs": resp.get("jobs", [])}
            f.write(json.dumps(line, ensure_ascii=False) + "\n")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: extract_transcript_searches.py <transcript.json>", file=sys.stderr)
        sys.exit(1)
    transcript_path = Path(sys.argv[1])
    data = json.loads(transcript_path.read_text())
    responses = collect_find_jobs_results(data)

    paired = []
    for i, spec in enumerate(KEYWORDS):
        if i < len(responses):
            resp = responses[i]
        else:
            resp = {"status": "error", "error_code": "MISSING_SEARCH"}
        paired.append({"keyword": spec["keyword"], "group": spec["group"], "response": resp})

    to_raw_jsonl(paired)
    ok = sum(1 for p in paired if p["response"].get("status") == "ok")
    missing = [p["keyword"] for p in paired if p["response"].get("error_code") == "MISSING_SEARCH"]
    print(json.dumps({"paired": len(paired), "responses": len(responses), "ok": ok, "missing": len(missing), "missing_keywords": missing[:20]}))


if __name__ == "__main__":
    main()
