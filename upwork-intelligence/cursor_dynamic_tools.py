"""Optional MCP bridge for _run_fetch_all.py (Cloud Agent).

When no in-process MCP client exists, append MCP results to
_search_queue.jsonl via _flush_batch.py from the agent, then run _run_hourly.py.
"""
from __future__ import annotations

import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
QUEUE = BASE / "_search_queue.jsonl"


def call_dynamic_tool(namespace: str, toolName: str, arguments: dict):
    return {
        "status": "error",
        "error_code": "NO_MCP_BRIDGE",
        "reason": (
            "Shell cannot call Upwork MCP; use CallDynamicTool in the agent and "
            "append results with _flush_batch.py"
        ),
    }
