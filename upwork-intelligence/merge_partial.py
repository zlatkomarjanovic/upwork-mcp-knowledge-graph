#!/usr/bin/env python3
"""Merge partial/batch_*.json into search_responses.json."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
partial = ROOT / "partial"
out = ROOT / "search_responses.json"
entries = []
if partial.is_dir():
    for p in sorted(partial.glob("batch_*.json")):
        entries.extend(json.loads(p.read_text()))
if out.exists():
    existing = json.loads(out.read_text())
    seen = {e.get("keyword") for e in existing}
    for e in entries:
        if e.get("keyword") not in seen:
            existing.append(e)
    out.write_text(json.dumps(existing, ensure_ascii=False))
else:
    out.write_text(json.dumps(entries, ensure_ascii=False))
print(json.dumps({"merged": len(entries), "total": len(json.loads(out.read_text()))}))
