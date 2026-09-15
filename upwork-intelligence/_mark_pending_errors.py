#!/usr/bin/env python3
"""Mark keywords without stored searches as error stubs so run log stays honest."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from _process_run import KEYWORD_GROUPS

path = Path(__file__).parent / "search-results-raw.json"
data = json.loads(path.read_text()) if path.exists() else {"searches": [], "errors": []}
done = {s["keyword"] for s in data["searches"]}
for group, kws in KEYWORD_GROUPS:
    for kw in kws:
        if kw in done:
            continue
        data["searches"].append({"keyword": kw, "group": group, "jobs": [], "error": True})
        data.setdefault("errors", []).append(kw)
path.write_text(json.dumps(data))
