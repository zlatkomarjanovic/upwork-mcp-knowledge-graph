#!/usr/bin/env python3
"""Expand anchor keyword cache files to full search_responses.json (93 keywords)."""
import json
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).parent
KW = json.loads((ROOT / "keywords.json").read_text())["keywords"]
CACHE = ROOT / "cache"

ANCHORS = {
    "CORE WEB DEVELOPMENT": "web development",
    "WEB DESIGN": "web design",
    "WORDPRESS": "wordpress developer",
    "WEBFLOW / FRAMER": "webflow developer",
    "AI / VIBE CODING": "vibe coding",
    "GOHIGHLEVEL": "gohighlevel developer",
    "ADJACENT PLATFORMS": "wix website",
    "MODERN STACK": "nextjs developer",
    "ECOMMERCE": "shopify developer",
    "MAINTENANCE / RETAINERS": "website maintenance",
    "CONVERSION / PERFORMANCE": "core web vitals",
}


def load_kw(kw: str) -> dict:
    p = CACHE / f"{quote(kw, safe='')}.json"
    if not p.exists():
        return {"status": "error", "error": "missing anchor cache"}
    return json.loads(p.read_text())["response"]


def main() -> None:
    anchor_resp = {g: load_kw(a) for g, a in ANCHORS.items()}
    out = []
    missing = []
    for kw, group in KW.items():
        resp = anchor_resp.get(group) or {"status": "error", "error": "missing group anchor"}
        if resp.get("status") == "error":
            missing.append(kw)
        out.append({"keyword": kw, "group": group, "response": resp})
    (ROOT / "search_responses.json").write_text(json.dumps(out, ensure_ascii=False))
    print(json.dumps({"keywords": len(out), "missing_anchors": missing[:5], "errors": len(missing)}))


if __name__ == "__main__":
    main()
