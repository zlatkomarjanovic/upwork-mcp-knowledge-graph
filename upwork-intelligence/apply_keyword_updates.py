#!/usr/bin/env python3
"""Apply keyword->response updates from JSON file to search_responses.json."""
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
    for k in ("error_code", "error", "hasMore", "next_cursor", "pageInfo", "client_rating_basis", "trace_id"):
        if k in resp:
            out[k] = resp[k]
    return out


def main() -> None:
    updates = json.loads(Path(sys.argv[1]).read_text())
    paired = json.loads(SEARCH.read_text())
    index = {e["keyword"]: i for i, e in enumerate(paired)}
    for item in updates:
        kw = item["keyword"]
        resp = slim(item["response"])
        entry = {"keyword": kw, "group": GROUPS.get(kw, "OTHER"), "response": resp}
        if kw in index:
            paired[index[kw]] = entry
        else:
            paired.append(entry)
    SEARCH.write_text(json.dumps(paired, indent=2))
    ok = sum(1 for e in paired if (e.get("response") or {}).get("status") == "ok")
    print(json.dumps({"total": len(paired), "ok": ok}))


if __name__ == "__main__":
    main()
