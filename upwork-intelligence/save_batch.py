#!/usr/bin/env python3
import json, hashlib, sys
from pathlib import Path
kw, group, path = sys.argv[1], sys.argv[2], sys.argv[3]
data = json.loads(Path(path).read_text())
slug = hashlib.md5(kw.encode()).hexdigest()[:12]
out = Path(__file__).resolve().parent / "raw_batches" / f"{slug}.json"
payload = {"keyword": kw, "group": group, "response": data}
if data.get("status") == "error":
    payload["error"] = True
Path(out).write_text(json.dumps(payload))
print(out)
