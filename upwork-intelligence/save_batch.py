#!/usr/bin/env python3
"""Alias: save MCP chunk JSON array to mcp_queue/."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ingest_chunk import main  # noqa: E402

if __name__ == "__main__":
    main()
