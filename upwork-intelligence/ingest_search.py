#!/usr/bin/env python3
import json, hashlib, sys
from pathlib import Path
BASE = Path(__file__).resolve().parent / "raw_batches"
BASE.mkdir(exist_ok=True)
data = json.loads(sys.stdin.read())
kw = data["keyword"]
group = data.get("group", "")
slug = hashlib.md5(kw.encode()).hexdigest()[:12]
(BASE / f"{slug}.json").write_text(json.dumps(data, ensure_ascii=False))
print(slug)
