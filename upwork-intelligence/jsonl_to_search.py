#!/usr/bin/env python3
"""Build search_responses.json from _search_batches.jsonl (latest line per keyword wins)."""
import json
from pathlib import Path

ROOT = Path(__file__).parent
BATCH = ROOT / "_search_batches.jsonl"
SEARCH = ROOT / "search_responses.json"
GROUPS = json.loads((ROOT / "keywords.json").read_text())["keywords"]


def main():
    latest: dict[str, list] = {}
    if BATCH.exists():
        for line in BATCH.read_text().splitlines():
            if not line.strip():
                continue
            o = json.loads(line)
            latest[o["keyword"]] = o.get("jobs") or []
    paired = []
    for kw, group in GROUPS.items():
        jobs = latest.get(kw)
        if jobs is None:
            resp = {"status": "error", "error_code": "MISSING_SEARCH"}
        else:
            resp = {"status": "ok", "jobs": jobs}
        paired.append({"keyword": kw, "group": group, "response": resp})
    SEARCH.write_text(json.dumps(paired, indent=2))
    ok = sum(1 for p in paired if p["response"].get("status") == "ok")
    miss = sum(1 for p in paired if p["response"].get("error_code") == "MISSING_SEARCH")
    print(json.dumps({"keywords": len(paired), "ok": ok, "missing": miss}))


if __name__ == "__main__":
    main()
