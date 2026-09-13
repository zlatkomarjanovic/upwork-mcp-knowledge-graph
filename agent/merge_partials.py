#!/usr/bin/env python3
"""Merge partial search JSON files into cycle-searches.json."""
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PARTIAL = ROOT / "partial"
OUT = ROOT / "cycle-searches.json"

def main():
    from datetime import datetime as dt

    slot = dt.now(timezone.utc).hour % 3
    from pathlib import Path
    import importlib.util

    cfg_path = ROOT / "scripts" / "keywords-config.mjs"
    # groups from slot via node
    import subprocess

    groups_json = subprocess.check_output(
        [
            "node",
            "-e",
            f"import {{ROTATION,slotForHour}} from './scripts/keywords-config.mjs';"
            f"const s=slotForHour(new Date().getUTCHours());"
            f"console.log(JSON.stringify({{slot:s,groups:ROTATION[s]}}));",
        ],
        cwd=ROOT,
        text=True,
    )
    meta_slot = json.loads(groups_json)
    slot = meta_slot["slot"]
    groups = meta_slot["groups"]

    searches = []
    if PARTIAL.exists():
        for p in sorted(PARTIAL.glob("*.json")):
            searches.append(json.loads(p.read_text()))
    keywords = [s["keyword"] for s in searches]
    jobs_returned = sum(len(s.get("jobs") or []) for s in searches)
    doc = {
        "meta": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "slot": slot,
            "groups": groups,
            "keywordsSearched": keywords,
            "jobsReturned": jobs_returned,
        },
        "searches": searches,
        "failures": [],
    }
    OUT.write_text(json.dumps(doc, indent=2))
    print(OUT, len(searches), jobs_returned)

if __name__ == "__main__":
    main()
