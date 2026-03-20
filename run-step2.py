"""Top-level launcher for Step 2 (ARS analysis + PPTX generation).

Delegates to step2-analysis/run.py.
"""
import subprocess
import sys
from pathlib import Path

step2_script = Path(__file__).parent / "step2-analysis" / "run.py"
sys.exit(subprocess.call([sys.executable, str(step2_script)] + sys.argv[1:]))
