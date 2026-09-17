#!/usr/bin/env python3
"""Replace _batch_results rows for keywords present in incoming JSON."""
import json, sys
from pathlib import Path
from append_mcp import normalize_row

BASE = Path(__file__).parent
OUT = BASE / "_batch_results.jsonl"

def main():
    path = Path(sys.argv[1])
    updates = json.loads(path.read_text())
    if not isinstance(updates, list):
        updates = [updates]
    by_kw = {u["keyword"]: normalize_row(u) for u in updates if u.get("keyword")}
    lines = []
    if OUT.exists():
        for line in OUT.read_text().splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            kw = row.get("keyword")
            if kw in by_kw:
                lines.append(json.dumps(by_kw.pop(kw), ensure_ascii=False))
                continue
            lines.append(line)
    for kw, row in by_kw.items():
        lines.append(json.dumps(row, ensure_ascii=False))
    OUT.write_text("\n".join(lines) + "\n")
    print("updated", len(updates), "keywords")

if __name__ == "__main__":
    main()
