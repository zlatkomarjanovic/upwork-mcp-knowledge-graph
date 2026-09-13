#!/usr/bin/env python3
"""Merge live_batches/*.json into search_responses.json for process_run."""
import json
from pathlib import Path

ROOT = Path(__file__).parent
GROUPS = json.loads((ROOT / "keywords.json").read_text())["keywords"]
BATCH_DIR = ROOT / "live_batches"
SEARCH = ROOT / "search_responses.json"


def slim(resp: dict) -> dict:
    jobs = []
    for j in resp.get("jobs") or []:
        jobs.append({k: v for k, v in j.items() if k != "description_snippet"})
    out = {"status": resp.get("status", "ok"), "jobs": jobs}
    for k in ("error_code", "error", "reason"):
        if k in resp:
            out[k] = resp[k]
    return out


def main() -> None:
    paired = []
    seen = set()
    for path in sorted(BATCH_DIR.glob("*.json")):
        batch = json.loads(path.read_text())
        for item in batch:
            kw = item["keyword"]
            if kw in seen:
                continue
            seen.add(kw)
            resp = item.get("response") or {}
            paired.append(
                {
                    "keyword": kw,
                    "group": GROUPS.get(kw, "OTHER"),
                    "response": slim(resp),
                }
            )
    # Ensure all keywords present (empty ok for missing)
    by_kw = {e["keyword"]: e for e in paired}
    ordered = []
    for kw, group in GROUPS.items():
        if kw in by_kw:
            ordered.append(by_kw[kw])
        else:
            ordered.append({"keyword": kw, "group": group, "response": {"status": "error", "error_code": "MISSING"}})
    SEARCH.write_text(json.dumps(ordered, indent=2))
    missing = [kw for kw in GROUPS if kw not in seen]
    print(json.dumps({"merged": len(seen), "missing": missing, "total": len(GROUPS)}))


if __name__ == "__main__":
    main()
