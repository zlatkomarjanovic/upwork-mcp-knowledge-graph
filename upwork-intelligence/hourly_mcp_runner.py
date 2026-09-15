#!/usr/bin/env python3
"""
Hourly keyword fetch helper (agent-driven).

Shell cannot call Upwork MCP. The automation agent must:
1. Call upwork__find_jobs for each keyword (batch ~4, persist after each batch).
2. Save responses: python3 save_batch.py /path/to/chunk.json
3. Run: ./run_pipeline.sh

chunk.json format: [{"keyword":"...", "group":"...", "response": {...MCP JSON...}}, ...]
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from process_run import ALL_KEYWORDS, KW_TO_GROUP  # noqa: E402

ORG = "1472686528932380673"


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--list":
        for kw in ALL_KEYWORDS:
            print(json.dumps({"keyword": kw, "group": KW_TO_GROUP[kw], "org_uid": ORG}))
        return
    print(
        json.dumps(
            {
                "org_uid": ORG,
                "keyword_count": len(ALL_KEYWORDS),
                "persist": "python3 save_batch.py chunk.json && ./run_pipeline.sh",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
