#!/usr/bin/env python3
"""Merge batches/*.json {keyword: mcp_response} into run-results.jsonl"""
import json
from pathlib import Path

from process_run import KEYWORD_GROUPS

BASE = Path(__file__).parent
OUT = BASE / "run-results.jsonl"
batch_dir = BASE / "batches"

kw_to_group = {}
for group, kws in KEYWORD_GROUPS.items():
    for kw in kws:
        kw_to_group[kw] = group

seen = set()
if OUT.exists():
    for line in OUT.read_text().splitlines():
        if line.strip():
            seen.add(json.loads(line)["keyword"])

with OUT.open("a") as out:
    for path in sorted(batch_dir.glob("*.json")):
        if path.name.startswith("_"):
            continue
        chunk = json.loads(path.read_text())
        for kw, resp in chunk.items():
            if kw in seen:
                continue
            jobs = resp.get("jobs") or []
            out.write(
                json.dumps(
                    {"keyword": kw, "group": kw_to_group.get(kw, ""), "jobs": jobs},
                    separators=(",", ":"),
                )
                + "\n"
            )
            seen.add(kw)
