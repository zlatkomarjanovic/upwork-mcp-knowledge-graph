#!/usr/bin/env python3
"""Ingest MCP batch JSON from stdin into search_responses.json via save_batch logic."""
import json
import subprocess
import sys

subprocess.run(
    [sys.executable, str(__import__("pathlib").Path(__file__).parent / "save_batch.py")],
    input=sys.stdin.read(),
    text=True,
    check=True,
)
