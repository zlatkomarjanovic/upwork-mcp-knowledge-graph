#!/usr/bin/env python3
"""Save list of {keyword, response} from JSON file to mcp_raw/."""
import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
OUT = BASE / "mcp_raw"
OUT.mkdir(exist_ok=True)


def slug(kw: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", kw.lower()).strip("_") or "kw"


def strip_resp(resp):
    if not isinstance(resp, dict):
        return resp
    out = dict(resp)
    jobs = out.get("jobs")
    if isinstance(jobs, list):
        for j in jobs:
            if isinstance(j, dict):
                j.pop("description_snippet", None)
    return out


def main():
    data = json.loads(Path(sys.argv[1]).read_text())
    items = data if isinstance(data, list) else data.get("searches", [])
    for item in items:
        kw = item["keyword"]
        (OUT / f"{slug(kw)}.json").write_text(
            json.dumps(
                {"keyword": kw, "response": strip_resp(item.get("response") or {})},
                ensure_ascii=False,
            )
        )
    print(len(items))


if __name__ == "__main__":
    main()
