#!/usr/bin/env python3
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent
kw, group, resp_path = sys.argv[1], sys.argv[2], sys.argv[3]
resp = json.loads(Path(resp_path).read_text())
jobs = resp.get("jobs") or []
if resp.get("status") == "error":
    line = {"keyword": kw, "group": group, "error": resp.get("error_code", "error")}
else:
    line = {"keyword": kw, "group": group, "jobs": jobs}
with (ROOT / "run-results.jsonl").open("a") as f:
    f.write(json.dumps(line, ensure_ascii=False) + "\n")
print(kw, len(jobs) if jobs else resp.get("error_code"))
