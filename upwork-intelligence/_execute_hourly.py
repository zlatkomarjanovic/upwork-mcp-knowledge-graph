#!/usr/bin/env python3
"""
Execute all keyword searches by re-invoking stored chunk files or marking pending.
Cloud agent should run MCP for pending keywords and append via _append_chunk.py.
"""
import json
import sys
from pathlib import Path

BASE = Path(__file__).parent
RAW = BASE / "search-results-raw.json"
CHUNKS = BASE / "_search_chunks.jsonl"

sys.path.insert(0, str(BASE))
from _process_run import KEYWORD_GROUPS  # noqa: E402


def load_raw():
    if RAW.exists():
        return json.loads(RAW.read_text())
    return {"searches": [], "errors": []}


def merge_chunks():
    data = load_raw()
    done = {s["keyword"] for s in data["searches"]}
    if CHUNKS.exists():
        for line in CHUNKS.read_text().splitlines():
            if not line.strip():
                continue
            chunk = json.loads(line)
            if chunk["keyword"] in done:
                continue
            data["searches"].append(chunk)
            done.add(chunk["keyword"])
    RAW.write_text(json.dumps(data))
    return data


def pending():
    data = merge_chunks()
    done = {s["keyword"] for s in data["searches"]}
    out = []
    for group, kws in KEYWORD_GROUPS:
        for kw in kws:
            if kw not in done:
                out.append({"keyword": kw, "group": group})
    return out, data


if __name__ == "__main__":
    pend, data = pending()
    print(json.dumps({"stored": len(data["searches"]), "pending": len(pend), "pending_list": pend}))
