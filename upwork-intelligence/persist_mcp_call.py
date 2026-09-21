#!/usr/bin/env python3
"""Usage: persist_mcp_call.py KEYWORD GROUP RESPONSE_JSON_FILE"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from save_mcp_compact import save_item  # noqa: E402

def main():
    kw, group, path = sys.argv[1], sys.argv[2], Path(sys.argv[3])
    resp = json.loads(path.read_text())
    save_item(kw, group, resp, resp.get("status") != "ok")
    print(kw, "ok" if resp.get("status") == "ok" else "err")

if __name__ == "__main__":
    main()
