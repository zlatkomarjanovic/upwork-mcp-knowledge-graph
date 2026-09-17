#!/usr/bin/env python3
"""Build search_responses.json from cache/ or mcp_raw/."""
import json
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).parent
KW = json.loads((ROOT / "keywords.json").read_text())["keywords"]
CACHE = ROOT / "cache"
RAW = ROOT / "mcp_raw"


def slug(kw: str) -> str:
    import re

    return re.sub(r"[^a-z0-9]+", "_", kw, flags=re.I).strip("_")[:80]


def load_response(kw: str) -> dict:
    c = CACHE / f"{quote(kw, safe='')}.json"
    if c.exists():
        return json.loads(c.read_text())["response"]
    r = RAW / f"{slug(kw)}.json"
    if r.exists():
        row = json.loads(r.read_text())
        if row.get("error"):
            return {"status": "error", "error": row["error"]}
        return {"status": "ok", "jobs": row.get("jobs") or []}
    return {"status": "error", "error": "not searched"}


def main() -> None:
    out = []
    for kw, group in KW.items():
        out.append({"keyword": kw, "group": group, "response": load_response(kw)})
    (ROOT / "search_responses.json").write_text(json.dumps(out, ensure_ascii=False))
    missing = [x["keyword"] for x in out if x["response"].get("status") == "error"]
    print(json.dumps({"total": len(out), "missing": len(missing), "missing_sample": missing[:10]}))


if __name__ == "__main__":
    main()
