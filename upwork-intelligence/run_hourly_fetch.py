#!/usr/bin/env python3
"""Emit keyword list for hourly MCP fetch (one keyword per line)."""
import json
from pathlib import Path

ROOT = Path(__file__).parent
keywords = json.loads((ROOT / "keywords.json").read_text())["keywords"]
for kw in keywords:
    print(kw)
