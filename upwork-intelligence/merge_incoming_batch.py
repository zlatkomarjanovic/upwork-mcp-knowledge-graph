#!/usr/bin/env python3
"""Append incoming JSON/JSONL search rows to _batch_results.jsonl (skip existing keywords)."""
import json
from pathlib import Path
from append_mcp import normalize_row

BASE = Path(__file__).parent
OUT = BASE / "_batch_results.jsonl"
INC = BASE / "incoming" / "r12"

def existing_keywords():
    s = set()
    if OUT.exists():
        for line in OUT.read_text().splitlines():
            if line.strip():
                s.add(json.loads(line).get("keyword"))
    return s

def ingest_path(path, have):
    if path.suffix == ".jsonl":
        rows = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
    else:
        data = json.loads(path.read_text())
        rows = data if isinstance(data, list) else [data]
    with OUT.open("a", encoding="utf-8") as f:
        for row in rows:
            kw = row.get("keyword")
            if not kw or kw in have:
                continue
            f.write(json.dumps(normalize_row(row), ensure_ascii=False) + "\n")
            have.add(kw)

def main():
    have = existing_keywords()
    if INC.exists():
        for p in sorted(INC.glob("*")):
            if p.is_file() and p.suffix in (".json", ".jsonl"):
                ingest_path(p, have)
    print("batch lines", sum(1 for _ in OUT.open()) if OUT.exists() else 0, "keywords", len(have))

if __name__ == "__main__":
    main()
