#!/usr/bin/env python3
"""Persist one MCP find_jobs tool result JSON from a file. Usage: persist_mcp_tool.py <keyword> <group> <response.json>"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from record_search import main as record_main  # noqa: E402

if __name__ == "__main__":
    record_main()
