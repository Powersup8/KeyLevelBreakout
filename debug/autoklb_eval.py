#!/usr/bin/env python3
"""
AutoKLB Eval Wrapper — runs catalog eval + real-data eval in sequence.
Output is the union of both scripts' stdout; agent greps:
  - train_score / val_score     → catalog metrics
  - rd_train_score / rd_val_score → real-data metrics
Keep/discard loop is based on rd_val_score.
"""
import subprocess
import sys
from pathlib import Path

DEBUG_DIR = Path(__file__).parent


def run(script):
    r = subprocess.run(
        [sys.executable, str(DEBUG_DIR / script)],
        capture_output=True, text=True, cwd=str(DEBUG_DIR),
    )
    if r.stdout:
        print(r.stdout, end="")
    if r.stderr:
        print(r.stderr, end="", file=sys.stderr)
    return r.returncode


rc1 = run("autoklb_prepare.py")
rc2 = run("autoklb_realdata.py")
sys.exit(0 if rc1 == 0 else rc1)
