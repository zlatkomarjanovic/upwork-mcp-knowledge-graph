#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
OUT = BASE / "mcp_raw"
OUT.mkdir(exist_ok=True)


def slug(kw: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", kw.lower()).strip("_") or "kw"


def strip_resp(resp: dict) -> dict:
    if not isinstance(resp, dict):
        return resp
    out = dict(resp)
    jobs = out.get("jobs")
    if isinstance(jobs, list):
        slim = []
        for j in jobs:
            if not isinstance(j, dict):
                continue
            slim.append({k: v for k, v in j.items() if k != "description_snippet"})
        out["jobs"] = slim
    return out


def main():
    path = Path(sys.argv[1])
    data = json.loads(path.read_text())
    items = data if isinstance(data, list) else data.get("searches", [data])
    for item in items:
        kw = item["keyword"]
        resp = strip_resp(item.get("response") or {})
        (OUT / f"{slug(kw)}.json").write_text(
            json.dumps({"keyword": kw, "response": resp}, ensure_ascii=False)
        )


if __name__ == "__main__":
    main()
