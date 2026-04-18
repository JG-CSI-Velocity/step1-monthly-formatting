"""Verify the --persona-module flag is wired into the CLI."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


_ASSEMBLER = (
    Path(__file__).resolve().parent.parent / "deck_assembler.py"
)


def test_persona_module_flag_documented_in_help():
    result = subprocess.run(
        [sys.executable, str(_ASSEMBLER), "--help"],
        capture_output=True,
        text=True,
    )
    # --help always exits 0
    assert result.returncode == 0
    assert "--persona-module" in result.stdout, (
        "CLI help should document the --persona-module flag"
    )
