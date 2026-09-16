#!/usr/bin/env python3
"""Merge keyword responses from live_responses.json into search_responses.json."""
import json
from pathlib import Path

ROOT = Path(__file__).parent
LIVE = ROOT / "live_responses.json"
SEARCH = ROOT / "search_responses.json"
GROUPS = json.loads((ROOT / "keywords.json").read_text())["keywords"]


def main() -> None:
    live = json.loads(LIVE.read_text()) if LIVE.exists() else {}
    paired = json.loads(SEARCH.read_text()) if SEARCH.exists() else []
    index = {e["keyword"]: i for i, e in enumerate(paired)}
    for kw in GROUPS:
        if kw not in live:
            continue
        entry = {"keyword": kw, "group": GROUPS[kw], "response": live[kw]}
        if kw in index:
            paired[index[kw]] = entry
        else:
            paired.append(entry)
            index[kw] = len(paired) - 1
    # Ensure all keywords present
    for kw, group in GROUPS.items():
        if kw not in index:
            paired.append(
                {
                    "keyword": kw,
                    "group": group,
                    "response": {"status": "error", "error_code": "MISSING_SEARCH"},
                }
            )
    paired.sort(key=lambda x: list(GROUPS.keys()).index(x["keyword"]))
    SEARCH.write_text(json.dumps(paired, indent=2))
    ok = sum(1 for p in paired if (p.get("response") or {}).get("status") == "ok")
    print(json.dumps({"merged": len(live), "total": len(paired), "ok": ok}))


if __name__ == "__main__":
    main()
