#!/usr/bin/env python3
"""Keyword list helper for hourly tracker (MCP searches run via agent)."""
from process_run import KEYWORD_GROUPS, ALL_KEYWORDS, KW_TO_GROUP

if __name__ == "__main__":
    import json
    print(json.dumps({"count": len(ALL_KEYWORDS), "keywords": ALL_KEYWORDS}, indent=2))
