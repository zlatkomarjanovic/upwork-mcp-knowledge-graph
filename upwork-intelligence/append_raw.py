#!/usr/bin/env python3
import json
import sys
from pathlib import Path

path = Path(__file__).parent / "raw-batch.json"
data = json.loads(path.read_text()) if path.exists() else []
entry = json.loads(sys.stdin.read())
data.append(entry)
path.write_text(json.dumps(data))
