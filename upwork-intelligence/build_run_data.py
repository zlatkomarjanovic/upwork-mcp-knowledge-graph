#!/usr/bin/env python3
"""Build run_data.jsonl from mcp_raw/*.json (one Upwork find_jobs response per keyword)."""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
RAW = BASE / "mcp_raw"
OUT = BASE / "run_data.jsonl"
KEYWORDS = json.loads((BASE / "keywords.json").read_text())
KEEP = (
    "url",
    "title",
    "published_date",
    "job_type",
    "budget",
    "duration",
    "experience_level",
    "proposals_tier",
    "skills",
    "client",
)


def slug(k: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in k).strip("_")[:120]


def compact_job(j):
    out = {x: j[x] for x in KEEP if x in j}
    if out.get("url"):
        out["url"] = out["url"].split("?")[0]
    return out


def main():
    OUT.write_text("")
    for row in KEYWORDS:
        kw, group = row["keyword"], row["group"]
        path = RAW / f"{slug(kw)}.json"
        line = {"keyword": kw, "group": group}
        if not path.exists():
            line["error"] = "not_completed_this_run"
        else:
            resp = json.loads(path.read_text())
            if resp.get("error"):
                line["error"] = resp["error"]
            elif resp.get("status") != "ok":
                line["error"] = resp.get("message") or "search_failed"
            else:
                line["jobs"] = [compact_job(j) for j in resp.get("jobs") or []]
        with OUT.open("a", encoding="utf-8") as f:
            f.write(json.dumps(line, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
