#!/usr/bin/env python3
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
raw = json.loads((BASE / "_raw_run.json").read_text())
done = {s["keyword"] for s in raw["searches"]}
all_kw = json.loads((BASE / "_keywords_all.json").read_text())
pending = [k for k in all_kw if k not in done]
print(json.dumps(pending))
