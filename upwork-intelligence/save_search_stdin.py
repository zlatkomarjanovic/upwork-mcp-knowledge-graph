#!/usr/bin/env python3
"""stdin: {keyword, group, response} -> raw_batches via save_mcp_compact."""
import json
import sys
from save_mcp_compact import save_item

def main():
    data = json.load(sys.stdin)
    save_item(data["keyword"], data["group"], data.get("response") or {}, data.get("error", False))
    print(data["keyword"])

if __name__ == "__main__":
    main()
