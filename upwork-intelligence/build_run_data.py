#!/usr/bin/env python3
"""Build batch_results.json from keywords.json + mcp_raw/*.json"""
import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent
RAW = BASE / "mcp_raw"


def slug(k: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", k.lower()).strip("-") or "kw"


def main():
    keywords = json.loads((BASE / "keywords.json").read_text())
    state_path = BASE / "state.json"
    run_number = 1
    window = 2
    if state_path.exists():
        st = json.loads(state_path.read_text())
        run_number = int(st.get("runNumber", 0)) + 1
        window = 1

    searches = []
    for item in keywords:
        kw, group = item["keyword"], item["group"]
        p = RAW / f"{slug(kw)}.json"
        entry = {"keyword": kw, "group": group}
        if p.exists():
            raw = json.loads(p.read_text())
            if raw.get("error"):
                entry["error"] = raw["error"]
            elif raw.get("status") != "ok":
                entry["error"] = raw.get("status")
            else:
                entry["jobs"] = raw.get("jobs") or []
        else:
            entry["error"] = "not_searched_this_run"
        searches.append(entry)

    batch = {
        "runNumber": run_number,
        "windowHours": window,
        "searches": searches,
    }
    (BASE / "batch_results.json").write_text(json.dumps(batch, ensure_ascii=False, indent=2))
    missing = sum(1 for s in searches if s.get("error") == "not_searched")
    failed = sum(1 for s in searches if s.get("error") and s.get("error") != "not_searched")
    print(json.dumps({"runNumber": run_number, "missing": missing, "failed": failed, "total": len(searches)}))


if __name__ == "__main__":
    main()
