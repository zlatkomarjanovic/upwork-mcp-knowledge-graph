#!/usr/bin/env python3
"""Build _search_queue.jsonl from _batches/responses/*.json (one MCP response per keyword slug)."""
import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent
KEYWORDS = json.loads((BASE / "keywords.json").read_text())
RESP = BASE / "_batches" / "responses"
QUEUE = BASE / "_search_queue.jsonl"


def slug(kw: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", kw.lower()).strip("_")


def strip_job(j):
    j = dict(j)
    j.pop("description_snippet", None)
    return j


def main():
    lines = []
    missing = []
    for item in KEYWORDS:
        kw, group = item["keyword"], item["group"]
        path = RESP / f"{slug(kw)}.json"
        if not path.exists():
            missing.append(kw)
            lines.append({"keyword": kw, "group": group, "status": "error", "error": "missing_response_file", "jobs": []})
            continue
        resp = json.loads(path.read_text())
        if resp.get("status") == "error" or resp.get("error_code"):
            lines.append({"keyword": kw, "group": group, "status": "error", "error": resp.get("reason") or resp.get("error_code"), "jobs": []})
        else:
            jobs = [strip_job(j) for j in (resp.get("jobs") or [])]
            lines.append({"keyword": kw, "group": group, "status": "ok", "jobs": jobs})
    with QUEUE.open("w") as f:
        for line in lines:
            f.write(json.dumps(line, ensure_ascii=False) + "\n")
    print(f"queue lines: {len(lines)}, missing: {len(missing)}")
    if missing:
        print("missing:", ", ".join(missing[:20]), "..." if len(missing) > 20 else "")


if __name__ == "__main__":
    main()
