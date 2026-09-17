#!/usr/bin/env python3
"""Write MCP round results to cache/. Input: JSON array of {keyword, response}."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
from save_batch import slim  # noqa: E402
from urllib.parse import quote

CACHE = ROOT / "cache"
CACHE.mkdir(exist_ok=True)


def main() -> None:
    batch = json.loads(Path(sys.argv[1]).read_text())
    for item in batch:
        kw = item["keyword"]
        resp = slim(item["response"])
        path = CACHE / f"{quote(kw, safe='')}.json"
        path.write_text(
            json.dumps({"keyword": kw, "response": resp}, ensure_ascii=False)
        )
    print(len(batch))


if __name__ == "__main__":
    main()
