#!/usr/bin/env python3
import json
import sys
from pathlib import Path

RAW = Path(__file__).parent / "raw_search_results.json"


def main():
    kw = sys.argv[1]
    resp = json.loads(Path(sys.argv[2]).read_text())
    data = {"searches": [], "errors": []}
    if RAW.exists():
        data = json.loads(RAW.read_text())
    if any(s["keyword"] == kw for s in data["searches"]):
        return
    if resp.get("status") == "ok" or resp.get("jobs"):
        data["searches"].append({"keyword": kw, "response": resp})
    else:
        data["errors"].append(kw)
    RAW.write_text(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
