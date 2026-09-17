#!/usr/bin/env python3
"""Merge mcp_batches/*.json into _batch_results.jsonl"""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
OUT = BASE / "_batch_results.jsonl"
BATCH_DIR = BASE / "mcp_batches"

def main():
    lines = []
    if BATCH_DIR.exists():
        for p in sorted(BATCH_DIR.glob("*.json")):
            data = json.loads(p.read_text())
            if isinstance(data, list):
                for row in data:
                    lines.append(json.dumps(row, separators=(",", ":")))
            else:
                lines.append(json.dumps(data, separators=(",", ":")))
    OUT.write_text("\n".join(lines) + ("\n" if lines else ""))
    print(f"Wrote {len(lines)} lines to {OUT}")

if __name__ == "__main__":
    main()
