#!/usr/bin/env python3
"""Run all Upwork keyword searches via Cursor MCP bridge (stdio JSON-RPC if available)."""
import json, re, sys, time, hashlib, subprocess
from pathlib import Path

ORG = "1472686528932380673"
BASE = Path(__file__).resolve().parent
RAW = BASE / "raw_batches"
RAW.mkdir(exist_ok=True)

# Import keyword list from processor
sys.path.insert(0, str(BASE))
from importlib.util import spec_from_loader, module_from_spec
import importlib.machinery
loader = importlib.machinery.SourceFileLoader("proc", str(BASE / ".run_process.py"))
spec = spec_from_loader("proc", loader)
proc = module_from_spec(spec)
loader.exec_module(proc)
KEYWORD_GROUPS = proc.KEYWORD_GROUPS

def slug(kw):
    return hashlib.md5(kw.encode()).hexdigest()[:12]

def already_done(kw):
    p = RAW / f"{slug(kw)}.json"
    if not p.exists():
        return False
    d = json.loads(p.read_text())
    return not d.get("error") and d.get("response", {}).get("status") == "ok"

keywords = []
for g, kws in KEYWORD_GROUPS.items():
    for kw in kws:
        keywords.append((kw, g))

pending = [(kw, g) for kw, g in keywords if not already_done(kw)]
print(f"Total {len(keywords)}, pending {len(pending)}", flush=True)

# Attempt via npx @modelcontextprotocol if configured — fallback: mark for agent
for i, (kw, g) in enumerate(pending):
    out = RAW / f"{slug(kw)}.json"
    # Placeholder: agent must fill via MCP; script only lists pending
    if not out.exists():
        out.write_text(json.dumps({"keyword": kw, "group": g, "pending": True}))
    if (i + 1) % 10 == 0:
        print(f"Prepared {i+1}/{len(pending)}", flush=True)

print("DONE_PREP", len(pending))
