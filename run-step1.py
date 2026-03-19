"""Top-level launcher for Step 1 (formatting).

Delegates to step1-formatting/run.py so the repo can be cloned
directly into M:\ARS\00_Formatting\00-Scripts\ and this file
sits at the root.
"""
import subprocess
import sys
from pathlib import Path

step1_script = Path(__file__).parent / "step1-formatting" / "run.py"
sys.exit(subprocess.call([sys.executable, str(step1_script)] + sys.argv[1:]))
