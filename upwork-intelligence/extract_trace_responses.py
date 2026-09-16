#!/usr/bin/env python3
"""Merge find_jobs transcript results into search_responses using trace_id -> keyword map."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MAP_FILE = ROOT / "trace_map.jsonl"
SEARCH = ROOT / "search_responses.json"
GROUPS = json.loads((ROOT / "keywords.json").read_text())["keywords"]


def slim(resp: dict) -> dict:
    jobs = []
    for j in resp.get("jobs") or []:
        jobs.append({k: v for k, v in j.items() if k != "description_snippet"})
    out: dict = {"status": resp.get("status", "ok"), "jobs": jobs}
    for k in ("error_code", "reason"):
        if k in resp:
            out[k] = resp[k]
    if resp.get("status") == "error" or resp.get("error_code"):
        out["status"] = "error"
    return out


def load_map() -> dict[str, str]:
    m: dict[str, str] = {}
    if not MAP_FILE.exists():
        return m
    for line in MAP_FILE.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        tid = row.get("trace_id")
        kw = row.get("keyword")
        if tid and kw:
            m[tid] = kw
    return m


def parse_results(data: dict) -> dict[str, dict]:
    by_trace: dict[str, dict] = {}
    for msg in data.get("messages") or []:
        if msg.get("role") != "tool" or msg.get("tool_name") != "mcp":
            continue
        value = (msg.get("tool_result") or {}).get("value") or {}
        if value.get("selectedTool") != "upwork__find_jobs":
            continue
        raw = value.get("result")
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except json.JSONDecodeError:
                raw = {"status": "error", "error_code": "PARSE_ERROR", "jobs": []}
        if not isinstance(raw, dict):
            continue
        tid = raw.get("trace_id")
        if tid:
            by_trace[tid] = slim(raw)
    return by_trace


def main() -> None:
    transcript = Path(sys.argv[1])
    data = json.loads(transcript.read_text())
    kw_map = load_map()
    by_trace = parse_results(data)

    paired = json.loads(SEARCH.read_text()) if SEARCH.exists() else []
    index = {e["keyword"]: i for i, e in enumerate(paired)}
    applied = 0
    missing_map = 0

    for tid, resp in by_trace.items():
        kw = kw_map.get(tid)
        if not kw or kw not in GROUPS:
            missing_map += 1
            continue
        entry = {"keyword": kw, "group": GROUPS[kw], "response": resp}
        if kw in index:
            paired[index[kw]] = entry
        else:
            paired.append(entry)
        applied += 1

    SEARCH.write_text(json.dumps(paired, indent=2))
    print(
        json.dumps(
            {
                "trace_results": len(by_trace),
                "mapped": applied,
                "missing_trace_map": missing_map,
                "map_entries": len(kw_map),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
