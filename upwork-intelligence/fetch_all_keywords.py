#!/usr/bin/env python3
"""
Fetch all configured keywords via Upwork MCP find_jobs.
Requires Cursor Cloud Agent MCP bridge (UPWORK_MCP_BRIDGE_URL) or manual batch JSON files.

When bridge is unset, merges existing search_batch_*.json only.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

from ingest_chunk import slim_response

ROOT = Path(__file__).resolve().parent
KEYWORDS = json.loads((ROOT / "keywords.json").read_text())
ORG_UID = os.environ.get("UPWORK_ORG_UID", "1472686528932380673")
BRIDGE = os.environ.get("UPWORK_MCP_BRIDGE_URL", "")
SLEEP = float(os.environ.get("UPWORK_SEARCH_SLEEP", "5.5"))


def mcp_find_jobs(query: str) -> dict:
    if not BRIDGE:
        raise RuntimeError("UPWORK_MCP_BRIDGE_URL not set")
    payload = json.dumps(
        {
            "namespace": "Upwork",
            "toolName": "upwork__find_jobs",
            "arguments": {
                "action": "search",
                "org_uid": ORG_UID,
                "params": {"query": query, "sort": "recency", "limit": 10},
            },
        }
    ).encode()
    req = urllib.request.Request(
        BRIDGE,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode())


def save_batch(batch_idx: int, entries: list) -> None:
    out = ROOT / f"search_batch_{batch_idx:03d}.json"
    out.write_text(json.dumps(entries, ensure_ascii=False))


def load_completed_keywords() -> set[str]:
    done: set[str] = set()
    for path in ROOT.glob("search_batch_*.json"):
        for entry in json.loads(path.read_text()):
            done.add(entry["keyword"])
    accum = ROOT / "search_accum.json"
    if accum.exists():
        for entry in json.loads(accum.read_text()):
            done.add(entry["keyword"])
    log_path = ROOT / "search_log.jsonl"
    if log_path.exists():
        with log_path.open() as f:
            for line in f:
                line = line.strip()
                if line:
                    done.add(json.loads(line)["keyword"])
    return done


def main() -> None:
    done = load_completed_keywords()
    pending = [k for k in KEYWORDS if k["keyword"] not in done]
    if not pending:
        print("All keywords already have batch files.")
        return
    if not BRIDGE:
        print(f"Pending {len(pending)} keywords; set UPWORK_MCP_BRIDGE_URL to auto-fetch.")
        return
    batch_idx = len(list(ROOT.glob("search_batch_*.json"))) + 1
    chunk: list = []
    for i, item in enumerate(pending):
        kw = item["keyword"]
        for attempt in range(3):
            try:
                resp = mcp_find_jobs(kw)
                break
            except urllib.error.HTTPError as e:
                if e.code == 429 and attempt < 2:
                    time.sleep(SLEEP * (attempt + 1))
                    continue
                resp = {"status": "error", "error": str(e)}
                break
            except Exception as e:  # noqa: BLE001
                resp = {"status": "error", "error": str(e)}
                break
        chunk.append({"keyword": kw, "group": item["group"], "response": resp})
        if len(chunk) >= 6:
            save_batch(batch_idx, chunk)
            batch_idx += 1
            chunk = []
        log_path = ROOT / "search_log.jsonl"
        row = {
            "keyword": kw,
            "group": item["group"],
            "response": slim_response(resp),
        }
        with log_path.open("a") as lf:
            lf.write(json.dumps(row, ensure_ascii=False) + "\n")
        if i < len(pending) - 1:
            time.sleep(SLEEP)
    if chunk:
        save_batch(batch_idx, chunk)
    print(f"Fetched {len(pending)} keywords into batch files.")


if __name__ == "__main__":
    main()
