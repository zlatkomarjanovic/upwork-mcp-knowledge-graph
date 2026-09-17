#!/usr/bin/env python3
"""Merge batch JSON files into raw_search_results.json."""
import json
import sys
from pathlib import Path

BASE = Path(__file__).parent
RAW = BASE / "raw_search_results.json"


def main():
    data = {"searches": [], "errors": []}
    if RAW.exists():
        data = json.loads(RAW.read_text())
    seen = {s["keyword"] for s in data["searches"]}
    for path in sys.argv[1:]:
        batch = json.loads(Path(path).read_text())
        for item in batch:
            kw = item["keyword"]
            if kw in seen:
                continue
            resp = item.get("response")
            if not resp or resp.get("status") not in ("ok", None) and not resp.get("jobs"):
                if kw not in data["errors"]:
                    data["errors"].append(kw)
                continue
            data["searches"].append({"keyword": kw, "response": resp})
            seen.add(kw)
    RAW.write_text(json.dumps(data, indent=2))
    print(json.dumps({"searches": len(data["searches"]), "errors": len(data["errors"])}))


if __name__ == "__main__":
    main()
