#!/usr/bin/env python3
"""Apply all JSON batch files from _batches/ into search_responses.json."""
import json
from pathlib import Path

ROOT = Path(__file__).parent
BATCH_DIR = ROOT / "_batches"
SEARCH = ROOT / "search_responses.json"
GROUPS = json.loads((ROOT / "keywords.json").read_text())["keywords"]
ORDER = list(GROUPS.keys())


def slim(resp: dict) -> dict:
    jobs = []
    for j in resp.get("jobs") or []:
        jobs.append({k: v for k, v in j.items() if k != "description_snippet"})
    out = {"status": resp.get("status", "ok"), "jobs": jobs}
    for k in ("error_code", "error"):
        if k in resp:
            out[k] = resp[k]
    return out


def main() -> None:
    paired = json.loads(SEARCH.read_text()) if SEARCH.exists() else []
    index = {e["keyword"]: i for i, e in enumerate(paired)}
    for path in sorted(BATCH_DIR.glob("*.json")):
        batch = json.loads(path.read_text())
        if isinstance(batch, dict) and "searches" in batch:
            items = batch["searches"]
        elif isinstance(batch, list):
            items = batch
        else:
            continue
        for item in items:
            kw = item["keyword"]
            entry = {
                "keyword": kw,
                "group": GROUPS.get(kw, "OTHER"),
                "response": slim(item["response"]),
            }
            if kw in index:
                paired[index[kw]] = entry
            else:
                paired.append(entry)
                index[kw] = len(paired) - 1
    paired.sort(key=lambda x: ORDER.index(x["keyword"]) if x["keyword"] in ORDER else 999)
    SEARCH.write_text(json.dumps(paired, indent=2))
    print(len(paired))


if __name__ == "__main__":
    main()
