#!/usr/bin/env python3
"""
Build cycle-searches.json by re-fetching all slot-0 keywords via Upwork MCP subprocess.
Uses cursor exec-daemon MCP bridge when UPWORK_MCP_JSON env is set; otherwise expects
partial/*.json files from record_search.py.
"""
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ORG = "1472686528932380673"
ROOT = Path(__file__).resolve().parent
OUT = ROOT / "cycle-searches.json"
PARTIAL = ROOT / "partial"

GROUPS = ["Core Web Dev", "Web Design", "WordPress", "Webflow/Framer"]

KEYWORDS = [
    ("Core Web Dev", "web development"),
    ("Core Web Dev", "website development"),
    ("Core Web Dev", "web developer"),
    ("Core Web Dev", "custom website"),
    ("Core Web Dev", "website builder"),
    ("Core Web Dev", "frontend developer"),
    ("Core Web Dev", "full stack developer"),
    ("Core Web Dev", "website project"),
    ("Web Design", "web design"),
    ("Web Design", "website design"),
    ("Web Design", "website redesign"),
    ("Web Design", "landing page design"),
    ("Web Design", "UI UX website"),
    ("Web Design", "responsive web design"),
    ("Web Design", "homepage redesign"),
    ("Web Design", "one page website"),
    ("WordPress", "wordpress"),
    ("WordPress", "wordpress developer"),
    ("WordPress", "wordpress website"),
    ("WordPress", "wordpress development"),
    ("WordPress", "wordpress redesign"),
    ("WordPress", "wordpress customization"),
    ("WordPress", "wordpress migration"),
    ("WordPress", "wordpress speed optimization"),
    ("WordPress", "wordpress maintenance"),
    ("WordPress", "woocommerce"),
    ("WordPress", "elementor developer"),
    ("WordPress", "bricks builder"),
    ("WordPress", "headless wordpress"),
    ("Webflow/Framer", "webflow"),
    ("Webflow/Framer", "webflow developer"),
    ("Webflow/Framer", "webflow website"),
    ("Webflow/Framer", "webflow redesign"),
    ("Webflow/Framer", "figma to webflow"),
    ("Webflow/Framer", "webflow CMS"),
    ("Webflow/Framer", "framer"),
    ("Webflow/Framer", "framer developer"),
    ("Webflow/Framer", "framer website"),
    ("Webflow/Framer", "framer redesign"),
    ("Webflow/Framer", "figma to framer"),
    ("Webflow/Framer", "framer CMS"),
]


def slug(keyword: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", keyword.lower()).strip("_")[:80]


def load_partial(keyword: str):
    p = PARTIAL / f"{slug(keyword)}.json"
    if p.exists():
        return json.loads(p.read_text())
    return None


def mcp_find_jobs(keyword: str) -> list:
    """Invoke Upwork find_jobs via external helper script if present."""
    helper = ROOT / "mcp_find_jobs.sh"
    if not helper.is_file():
        return None
    proc = subprocess.run(
        [str(helper), keyword],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr or proc.stdout)
    data = json.loads(proc.stdout)
    return data.get("jobs") or []


def main():
    searches = []
    failures = []
    for i, (group, keyword) in enumerate(KEYWORDS):
        entry = load_partial(keyword)
        if entry:
            searches.append(entry)
            continue
        try:
            jobs = mcp_find_jobs(keyword)
            if jobs is None:
                failures.append({"keyword": keyword, "group": group, "error": "no partial and no mcp helper"})
                continue
            entry = {"keyword": keyword, "group": group, "jobs": jobs}
            PARTIAL.mkdir(parents=True, exist_ok=True)
            (PARTIAL / f"{slug(keyword)}.json").write_text(json.dumps(entry, indent=2))
            searches.append(entry)
        except Exception as e:
            failures.append({"keyword": keyword, "group": group, "error": str(e)})
        if (i + 1) % 4 == 0 and i + 1 < len(KEYWORDS):
            time.sleep(6)

    # Preserve keyword order from KEYWORDS
    by_kw = {s["keyword"]: s for s in searches}
    ordered = [by_kw[kw] for g, kw in KEYWORDS if kw in by_kw]

    jobs_returned = sum(len(s.get("jobs") or []) for s in ordered)
    doc = {
        "meta": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "slot": 0,
            "groups": GROUPS,
            "keywordsSearched": [kw for _, kw in KEYWORDS],
            "jobsReturned": jobs_returned,
        },
        "searches": ordered,
        "failures": failures,
    }
    OUT.write_text(json.dumps(doc, indent=2))
    print(len(ordered), jobs_returned, OUT)
    return 0 if len(ordered) == len(KEYWORDS) else 1


if __name__ == "__main__":
    sys.exit(main())
