#!/usr/bin/env python3
"""Flush responses_data.ALL to mcp_raw via record_batch.save_item."""
from record_batch import save_item

try:
    from responses_data import ALL
except ImportError:
    ALL = []


def main():
    for item in ALL:
        save_item(item["keyword"], item["response"])
    print("persisted", len(ALL))


if __name__ == "__main__":
    main()
