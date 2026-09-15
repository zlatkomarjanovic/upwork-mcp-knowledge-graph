#!/usr/bin/env python3
"""Read stdin lines: KEYWORD<TAB>JSON_RESPONSE and save each."""
import json
import sys
from record_batch import save_item  # type: ignore


def main():
    n = 0
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        kw, _, rest = line.partition("\t")
        resp = json.loads(rest)
        save_item(kw, resp)
        n += 1
    print("saved", n)


if __name__ == "__main__":
    main()
