#!/usr/bin/env python3
"""Extract find_jobs MCP results from cloud agent transcript."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
META = json.loads((ROOT / "keywords.json").read_text())
GROUPS = META["keywords"]
ORDER = list(GROUPS.keys())


def collect_find_jobs(data: dict) -> list[tuple[str | None, dict]]:
    out: list[tuple[str | None, dict]] = []
    for m in data.get("messages") or []:
        if m.get("role") != "tool" or m.get("tool_name") != "mcp":
            continue
        value = (m.get("tool_result") or {}).get("value") or {}
        if value.get("selectedTool") != "upwork__find_jobs":
            continue
        args = value.get("arguments") or {}
        params = (args.get("arguments") or args).get("params") or args.get("params") or {}
        kw = params.get("query")
        raw = value.get("result")
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except json.JSONDecodeError:
                raw = {"status": "error", "error_code": "PARSE_ERROR"}
        out.append((kw, raw))
    return out


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: extract_transcript_searches.py <transcript.json>", file=sys.stderr)
        sys.exit(1)
    data = json.loads(Path(sys.argv[1]).read_text())
    searches = collect_find_jobs(data)
    by_kw: dict[str, dict] = {}
    for kw, resp in searches:
        if kw:
            by_kw[kw] = resp

    search_path = ROOT / "search_responses.json"
    paired = json.loads(search_path.read_text()) if search_path.exists() else []
    index = {e["keyword"]: i for i, e in enumerate(paired)}
    applied = 0
    for kw, resp in by_kw.items():
        if kw not in GROUPS:
            continue
        entry = {"keyword": kw, "group": GROUPS[kw], "response": resp}
        if kw in index:
            paired[index[kw]] = entry
        else:
            paired.append(entry)
            index[kw] = len(paired) - 1
        applied += 1
    missing = [kw for kw in ORDER if kw not in by_kw]

    search_path.write_text(json.dumps(paired, indent=2))
    ok = sum(1 for p in paired if (p.get("response") or {}).get("status") == "ok")
    print(json.dumps({"transcript_searches": len(searches), "applied": applied, "unique_keywords": len(by_kw), "ok_entries": ok, "missing_from_transcript": len(missing)}))


if __name__ == "__main__":
    main()
