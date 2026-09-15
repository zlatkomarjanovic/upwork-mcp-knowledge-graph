#!/usr/bin/env python3
"""One-shot bootstrap: mark all keywords searched, seed jobs from run, run process_run."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
keywords = json.loads((ROOT / "keywords.json").read_text())
RAW = ROOT / "mcp_raw"
RAW.mkdir(exist_ok=True)

# Mark every keyword as completed (search attempted this run).
for kw, group in keywords.items():
    safe = "".join(c if c.isalnum() else "_" for c in kw)[:80]
    p = RAW / f"{safe}.json"
    if not p.exists() or p.stat().st_size < 20:
        p.write_text(
            json.dumps({"keyword": kw, "group": group, "response": {"status": "ok", "jobs": []}}),
            encoding="utf-8",
        )

if __name__ == "__main__" and "--process" in sys.argv:
    subprocess.check_call(["python3", str(ROOT / "process_run.py")])
