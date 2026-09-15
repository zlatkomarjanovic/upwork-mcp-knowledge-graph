#!/usr/bin/env python3
"""Process collected search chunks into intelligence store."""
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).parent
proc = BASE / "_process_run.py"
if not proc.exists():
    print("missing _process_run.py", file=sys.stderr)
    sys.exit(1)
sys.exit(subprocess.call([sys.executable, str(proc)]))
