#!/usr/bin/env python3
"""Extract last N Upwork find_jobs MCP results from agent transcript, then process_run."""
import glob
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
EXTRACT = ROOT / "extract_transcript_searches.py"
PROCESS = ROOT / "process_run.py"


def latest_transcript() -> Path | None:
    base = Path("/tmp/cursor/cloud-agent-transcripts")
    if not base.exists():
        return None
    dirs = sorted(base.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
    for d in dirs:
        for t in d.glob("*/transcript.json"):
            return t
    return None


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else latest_transcript()
    if not path or not path.exists():
        print("No transcript found", file=sys.stderr)
        sys.exit(1)
    subprocess.check_call([sys.executable, str(EXTRACT), str(path)])
    subprocess.check_call([sys.executable, str(PROCESS)])
    print("done", path)


if __name__ == "__main__":
    main()
