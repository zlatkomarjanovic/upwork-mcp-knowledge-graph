#!/usr/bin/env python3
"""Apply slim MCP capture into search_responses.json (keywords 0-27)."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
GROUPS = json.loads((ROOT / "keywords.json").read_text())["keywords"]
SLIM = ROOT / "slim_28.json"
SEARCH = ROOT / "search_responses.json"

RESTRICTED = {
    "status": "error",
    "error_code": "CLIENT",
    "reason": "Search restricted due to rate limit / ToS",
}


def main() -> None:
    slim = json.loads(SLIM.read_text())
    paired = json.loads(SEARCH.read_text())
    by_kw = {e["keyword"]: i for i, e in enumerate(paired)}
    for kw, resp in slim.items():
        if kw not in by_kw:
            continue
        paired[by_kw[kw]] = {
            "keyword": kw,
            "group": GROUPS[kw],
            "response": resp,
        }
    SEARCH.write_text(json.dumps(paired, indent=2))
    ok = sum(1 for p in paired if (p.get("response") or {}).get("status") == "ok")
    err = sum(1 for p in paired if (p.get("response") or {}).get("status") == "error")
    print(json.dumps({"ok": ok, "error": err, "total": len(paired)}))


if __name__ == "__main__":
    main()
