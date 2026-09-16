#!/usr/bin/env python3
import json
import sys
from pathlib import Path

from write_cache_batch import slim

ROOT = Path(__file__).parent
SEARCH = ROOT / "search_responses.json"
ORDER = list(json.loads((ROOT / "keywords.json").read_text())["keywords"].keys())
GROUPS = json.loads((ROOT / "keywords.json").read_text())["keywords"]


def main() -> None:
    kw, resp_path = sys.argv[1], sys.argv[2]
    resp = json.loads(Path(resp_path).read_text())
    paired = json.loads(SEARCH.read_text())
    by_kw = {p["keyword"]: p for p in paired}
    by_kw[kw] = {
        "keyword": kw,
        "group": GROUPS.get(kw, "OTHER"),
        "response": slim(resp),
    }
    paired = [by_kw[k] for k in ORDER if k in by_kw]
    SEARCH.write_text(json.dumps(paired, indent=2))


if __name__ == "__main__":
    main()
