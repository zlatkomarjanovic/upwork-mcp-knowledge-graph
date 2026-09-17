#!/usr/bin/env python3
"""Apply batch JSON file(s) of {keyword, response} into search_responses.json."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent
SEARCH = ROOT / "search_responses.json"
GROUPS = json.loads((ROOT / "keywords.json").read_text())["keywords"]


def slim(resp: dict) -> dict:
    jobs = []
    for j in resp.get("jobs") or []:
        jobs.append({k: v for k, v in j.items() if k != "description_snippet"})
    out: dict = {"status": resp.get("status", "ok"), "jobs": jobs}
    for k in ("error_code", "reason"):
        if k in resp:
            out[k] = resp[k]
    if resp.get("status") == "error" or resp.get("error_code"):
        out["status"] = "error"
    return out


def apply_batch(batch: list) -> int:
    paired = json.loads(SEARCH.read_text()) if SEARCH.exists() else []
    index = {e["keyword"]: i for i, e in enumerate(paired)}
    applied = 0
    for item in batch:
        kw = item["keyword"]
        if kw not in GROUPS:
            continue
        entry = {"keyword": kw, "group": GROUPS[kw], "response": slim(item["response"])}
        if kw in index:
            paired[index[kw]] = entry
        else:
            paired.append(entry)
        applied += 1
    SEARCH.write_text(json.dumps(paired, indent=2))
    return applied


def main() -> None:
    total = 0
    for path in sys.argv[1:]:
        batch = json.loads(Path(path).read_text())
        if isinstance(batch, dict) and "entries" in batch:
            batch = batch["entries"]
        total += apply_batch(batch)
    print(json.dumps({"applied": total}))


if __name__ == "__main__":
    main()
