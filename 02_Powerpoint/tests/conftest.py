"""Pytest config for 02_Powerpoint tests.

Adds the parent 02_Powerpoint directory to sys.path so section modules can
import from `._base` and siblings without requiring install.
"""

from __future__ import annotations

import sys
from pathlib import Path

_POWERPOINT = Path(__file__).resolve().parent.parent
if str(_POWERPOINT) not in sys.path:
    sys.path.insert(0, str(_POWERPOINT))
