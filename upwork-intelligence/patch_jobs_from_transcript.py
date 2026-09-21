#!/usr/bin/env python3
"""Append in-window jobs from transcript find_jobs into jobs.jsonl (dedupe by URL)."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from process_run import job_from_api, in_window, load_jobs_index, norm_url, KEYWORDS  # noqa: E402

JOBS_FILE = ROOT / "jobs.jsonl"
SEARCH_FILE = ROOT / "search_responses.json"


def collect_jobs(transcript_path: Path) -> list[dict]:
    data = json.loads(transcript_path.read_text())
    out = []
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
                continue
        if raw.get("status") != "ok":
            continue
        for j in raw.get("jobs") or []:
            out.append(j)
    return out


def keyword_for_url(url: str) -> tuple[str, str]:
    u = norm_url(url)
    if SEARCH_FILE.exists():
        for entry in json.loads(SEARCH_FILE.read_text()):
            for j in (entry.get("response") or {}).get("jobs") or []:
                if norm_url(j.get("url", "")) == u:
                    return entry["keyword"], entry["group"]
    return "transcript", "OTHER"


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: patch_jobs_from_transcript.py <transcript.json> [window_hours]", file=sys.stderr)
        sys.exit(1)
    transcript = Path(sys.argv[1])
    window_h = float(sys.argv[2]) if len(sys.argv) > 2 else 1.25
    state_path = ROOT / "state.json"
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    known = set(state.get("knownJobUrls") or [])
    jobs_index = load_jobs_index()
    if not known:
        known = set(jobs_index.keys())

    raw_jobs = collect_jobs(transcript)
    by_url: dict[str, dict] = {}
    for raw in raw_jobs:
        u = norm_url(raw.get("url") or "")
        if u:
            by_url[u] = raw

    new_rows = []
    for u, raw in by_url.items():
        kw, group = keyword_for_url(u)
        j = job_from_api(raw, kw, group)
        if not j or not in_window(j.get("postedAt"), window_h):
            continue
        if u in jobs_index:
            ex = jobs_index[u]
            if kw not in ex["matchedKeyword"] and kw != "transcript":
                ex["matchedKeyword"].append(kw)
            continue
        if u in known:
            continue
        new_rows.append(j)
        known.add(u)
        jobs_index[u] = j

    with JOBS_FILE.open("a") as f:
        for j in new_rows:
            f.write(json.dumps(j) + "\n")
    print(json.dumps({"patched": len(new_rows), "unique_transcript_jobs": len(by_url)}))


if __name__ == "__main__":
    main()
