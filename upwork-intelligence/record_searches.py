#!/usr/bin/env python3
"""Append MCP search rows to _batch_results.jsonl (stdin: JSON array or one object)."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent
BATCH = ROOT / "_batch_results.jsonl"
GROUPS = json.loads((ROOT / "keywords.json").read_text())["keywords"]


def slim_job(j: dict) -> dict:
    return {k: v for k, v in j.items() if k != "description_snippet"}


def slim_response(resp: dict) -> dict:
    out = {k: v for k, v in resp.items() if k not in ("description_snippet", "client_rating_basis")}
    if "jobs" in out:
        out["jobs"] = [slim_job(j) for j in out["jobs"]]
    return out


def main() -> None:
    raw = sys.stdin.read().strip()
    if not raw:
        return
    data = json.loads(raw)
    rows = data if isinstance(data, list) else [data]
    with BATCH.open("a") as f:
        for row in rows:
            kw = row["keyword"]
            resp = row.get("response") or row.get("mcp") or {}
            entry = {
                "keyword": kw,
                "group": GROUPS.get(kw, row.get("group", "OTHER")),
                "response": slim_response(resp),
            }
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(len(rows))


if __name__ == "__main__":
    main()
