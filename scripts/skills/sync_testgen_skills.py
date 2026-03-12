#!/usr/bin/env python3
"""Backward-compatible testgen family sync wrapper."""

from __future__ import annotations

from pathlib import Path
import runpy
import sys


if __name__ == "__main__":
    script = Path(__file__).resolve().parent / "sync_repo_skills.py"
    sys.argv = [str(script), "--family", "testgen", *sys.argv[1:]]
    runpy.run_path(str(script), run_name="__main__")
