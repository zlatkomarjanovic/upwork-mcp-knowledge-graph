#!/usr/bin/env python3
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent
SEARCH = ROOT / "search_responses.json"
GROUPS = json.loads((ROOT / "keywords.json").read_text())["keywords"]


def slim(resp):
    jobs = [{k: v for k, v in j.items() if k != "description_snippet"} for j in resp.get("jobs") or []]
    out = {"status": resp.get("status", "ok"), "jobs": jobs}
    if resp.get("error_code"):
        out["error_code"] = resp["error_code"]
    return out


def main():
    kw, resp_path = sys.argv[1], sys.argv[2]
    resp = slim(json.loads(Path(resp_path).read_text()))
    paired = json.loads(SEARCH.read_text())
    for e in paired:
        if e["keyword"] == kw:
            e["response"] = resp
            break
    else:
        paired.append({"keyword": kw, "group": GROUPS.get(kw, "OTHER"), "response": resp})
    SEARCH.write_text(json.dumps(paired, indent=2))
    print(kw)


if __name__ == "__main__":
    main()
