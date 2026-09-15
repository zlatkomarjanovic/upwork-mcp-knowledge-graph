#!/usr/bin/env python3
"""Pair the last N find_jobs transcript results with N keywords (search order)."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent
SEARCH = ROOT / "search_responses.json"
INGEST = ROOT / "ingest_batch.py"


def collect_find_jobs(data: dict) -> list[dict]:
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
    transcript = Path(sys.argv[1])
    keywords = sys.argv[2:]
    if not keywords:
        print("usage: ingest_transcript_tail.py transcript.json kw1 kw2 ...", file=sys.stderr)
        sys.exit(1)
    data = json.loads(transcript.read_text())
    all_res = collect_find_jobs(data)
    n = len(keywords)
    if len(all_res) < n:
        print(json.dumps({"error": "not enough searches", "have": len(all_res), "need": n}))
        sys.exit(1)
    tail = all_res[-n:]
    batch = [{"keyword": kw, "response": resp} for kw, resp in zip(keywords, tail)]
    batch_path = ROOT / "_tail_batch.json"
    batch_path.write_text(json.dumps(batch))
    import subprocess

    subprocess.check_call([sys.executable, str(INGEST), str(batch_path)])
    ok = sum(1 for x in tail if x.get("status") == "ok")
    print(json.dumps({"keywords": n, "ok": ok}))


if __name__ == "__main__":
    main()
