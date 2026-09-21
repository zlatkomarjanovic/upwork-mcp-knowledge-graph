#!/usr/bin/env python3
"""Merge keyword->response map into search_responses.json (slim jobs)."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent
SEARCH = ROOT / "search_responses.json"
GROUPS = json.loads((ROOT / "keywords.json").read_text())["keywords"]


def slim(resp: dict) -> dict:
    jobs = [{k: v for k, v in j.items() if k != "description_snippet"} for j in (resp.get("jobs") or [])]
    out = {"status": resp.get("status", "ok"), "jobs": jobs}
    for k in ("error_code", "error"):
        if k in resp:
            out[k] = resp[k]
    return out


def main():
    updates = json.loads(Path(sys.argv[1]).read_text())
    paired = json.loads(SEARCH.read_text())
    index = {e["keyword"]: i for i, e in enumerate(paired)}
    for kw, resp in updates.items():
        entry = {"keyword": kw, "group": GROUPS[kw], "response": slim(resp)}
        if kw in index:
            paired[index[kw]] = entry
        else:
            paired.append(entry)
    SEARCH.write_text(json.dumps(paired, indent=2))
    ok = sum(1 for p in paired if (p.get("response") or {}).get("status") == "ok" and (p.get("response") or {}).get("error_code") != "MISSING_SEARCH")
    miss = sum(1 for p in paired if (p.get("response") or {}).get("error_code") == "MISSING_SEARCH")
    print(json.dumps({"ok": ok, "missing": miss, "total": len(paired)}))


if __name__ == "__main__":
    main()
