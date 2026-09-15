#!/usr/bin/env python3
"""Save one MCP find_jobs response: python3 _save_mcp.py 'keyword' 'GROUP' /path/to/response.json"""
import json
import sys
from pathlib import Path

kw, group, resp_path = sys.argv[1], sys.argv[2], Path(sys.argv[3])
resp = json.loads(resp_path.read_text())
slug = kw.replace("/", "_").replace(" ", "_").replace(".", "")[:80]
out = Path(__file__).parent / "mcp_inbox" / f"{slug}.json"
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps({"keyword": kw, "group": group, "response": resp}, ensure_ascii=False))
print(out)
