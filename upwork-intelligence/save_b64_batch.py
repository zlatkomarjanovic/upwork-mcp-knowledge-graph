#!/usr/bin/env python3
"""Read lines: KEYWORD<TAB>base64_json. Append compact results to search_log.jsonl."""
import base64
import json
import sys
from pathlib import Path

from log_batch import compact

LOG = Path(__file__).parent / "search_log.jsonl"


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        kw, b64 = line.split("\t", 1)
        resp = json.loads(base64.b64decode(b64))
        LOG.open("a").write(
            json.dumps({"kw": kw, "result": compact(resp)}, separators=(",", ":")) + "\n"
        )


if __name__ == "__main__":
    main()
