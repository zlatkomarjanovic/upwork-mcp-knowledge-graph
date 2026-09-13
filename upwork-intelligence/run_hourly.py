#!/usr/bin/env python3
"""Hourly Upwork keyword tracker entrypoint."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
KEYWORDS = json.loads((ROOT / "keywords.json").read_text())


def completed_keywords() -> set[str]:
    done: set[str] = set()
    for path in ROOT.glob("search_batch_*.json"):
        for entry in json.loads(path.read_text()):
            done.add(entry["keyword"])
    accum = ROOT / "search_accum.json"
    if accum.exists():
        for entry in json.loads(accum.read_text()):
            done.add(entry["keyword"])
    log_path = ROOT / "search_log.jsonl"
    if log_path.exists():
        with log_path.open() as f:
            for line in f:
                line = line.strip()
                if line:
                    done.add(json.loads(line)["keyword"])
    return done


def main() -> int:
    done = completed_keywords()
    pending = [k["keyword"] for k in KEYWORDS if k["keyword"] not in done]
    is_first = not (ROOT / "state.json").exists() or not json.loads(
        (ROOT / "state.json").read_text()
    ).get("firstRunComplete")
    window = 2.0 if is_first else 1.0

    meta = {
        "attempted": [k["keyword"] for k in KEYWORDS],
        "completed": sorted(done),
        "failed": pending,
        "errors": [],
    }
    if pending:
        meta["errors"].append(
            f"{len(pending)} keywords missing batch files; run MCP searches before process_run"
        )
    (ROOT / "run_meta.json").write_text(json.dumps(meta, indent=2))

    if len(done) < len(KEYWORDS):
        print(
            f"WARNING: {len(done)}/{len(KEYWORDS)} keywords have saved searches. "
            f"Pending: {', '.join(pending[:10])}{'...' if len(pending) > 10 else ''}"
        )
        if len(done) == 0:
            return 2

    subprocess.check_call(
        [sys.executable, str(ROOT / "process_run.py"), str(window)],
        cwd=str(ROOT),
    )
    return 0 if not pending else 1


if __name__ == "__main__":
    raise SystemExit(main())
