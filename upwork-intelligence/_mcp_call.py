#!/usr/bin/env python3
"""Bridge hook for fetch_keywords.py — requires agent-side MCP; not available in bare shell."""
import json
import sys

print(json.dumps({"error": "MCP bridge not available in shell; use Upwork MCP from the agent or populate inbox/"}))
sys.exit(1)
