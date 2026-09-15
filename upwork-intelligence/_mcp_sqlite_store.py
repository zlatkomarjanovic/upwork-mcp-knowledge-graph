#!/usr/bin/env python3
"""Store MCP search responses in SQLite for hourly queue export."""
import json
import sqlite3
import sys
from pathlib import Path

DB = Path(__file__).resolve().parent / "_mcp_responses.db"


def init_db():
    con = sqlite3.connect(DB)
    con.execute(
        """CREATE TABLE IF NOT EXISTS responses (
        keyword TEXT PRIMARY KEY,
        grp TEXT,
        response_json TEXT NOT NULL
    )"""
    )
    con.commit()
    con.close()


def store(keyword, group, resp_path):
    init_db()
    resp = Path(resp_path).read_text()
    con = sqlite3.connect(DB)
    con.execute(
        "INSERT OR REPLACE INTO responses(keyword, grp, response_json) VALUES (?,?,?)",
        (keyword, group, resp),
    )
    con.commit()
    con.close()


def strip_job(j):
    j = dict(j)
    j.pop("description_snippet", None)
    return j


def export_queue():
    init_db()
    keywords = json.loads((Path(__file__).resolve().parent / "keywords.json").read_text())
    con = sqlite3.connect(DB)
    rows = {r[0]: (r[1], r[2]) for r in con.execute("SELECT keyword, grp, response_json FROM responses")}
    con.close()
    queue = Path(__file__).resolve().parent / "_search_queue.jsonl"
    missing = []
    with queue.open("w") as f:
        for item in keywords:
            kw, group = item["keyword"], item["group"]
            if kw not in rows:
                missing.append(kw)
                f.write(
                    json.dumps(
                        {
                            "keyword": kw,
                            "group": group,
                            "status": "error",
                            "error": "missing_mcp_response",
                            "jobs": [],
                        }
                    )
                    + "\n"
                )
                continue
            _, resp_raw = rows[kw][0], rows[kw][1]
            resp = json.loads(resp_raw)
            if resp.get("status") == "error" or resp.get("error_code"):
                line = {
                    "keyword": kw,
                    "group": group,
                    "status": "error",
                    "error": resp.get("reason") or resp.get("error_code"),
                    "jobs": [],
                }
            else:
                jobs = [strip_job(j) for j in (resp.get("jobs") or [])]
                line = {"keyword": kw, "group": group, "status": "ok", "jobs": jobs}
            f.write(json.dumps(line, ensure_ascii=False) + "\n")
    print("exported queue, missing", len(missing))
    return missing


if __name__ == "__main__":
    if sys.argv[1] == "export":
        missing = export_queue()
        if missing:
            sys.exit(2)
    else:
        store(sys.argv[1], sys.argv[2], sys.argv[3])
