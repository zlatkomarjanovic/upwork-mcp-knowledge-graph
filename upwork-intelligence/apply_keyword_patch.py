#!/usr/bin/env python3
"""Merge one or more keyword response JSON files into search_responses.json."""
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
    out = {"status": resp.get("status", "ok"), "jobs": jobs}
    for k in ("error_code", "error"):
        if k in resp:
            out[k] = resp[k]
    return out


def main() -> None:
    paired = json.loads(SEARCH.read_text())
    index = {e["keyword"]: i for i, e in enumerate(paired)}
    for path in sys.argv[1:]:
        data = json.loads(Path(path).read_text())
        kw = data.get("keyword") or Path(path).stem.replace("%20", " ")
        resp = slim(data.get("response") or data)
        entry = {"keyword": kw, "group": GROUPS.get(kw, "OTHER"), "response": resp}
        if kw in index:
            paired[index[kw]] = entry
        else:
            paired.append(entry)
            index[kw] = len(paired) - 1
    SEARCH.write_text(json.dumps(paired, indent=2))
    print("patched", len(sys.argv[1:]))


if __name__ == "__main__":
    main()
