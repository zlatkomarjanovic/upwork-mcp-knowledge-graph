#!/usr/bin/env python3
import json
import sys
from pathlib import Path

BASE = Path(__file__).parent
(BASE / "parts").mkdir(exist_ok=True)
data = json.loads(Path(sys.argv[1]).read_text())
fname = f"{int(sys.argv[2]):03d}_{data['keyword'][:40].replace('/', '_')}.json"
(BASE / "parts" / fname).write_text(json.dumps(data))
