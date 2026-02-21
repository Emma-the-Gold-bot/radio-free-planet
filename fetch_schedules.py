#!/usr/bin/env python3
"""
Compatibility entry point for the new tiered schedule pipeline.

This script intentionally stays at repository root so existing automation that
invokes `python fetch_schedules.py` keeps working.
"""

from pathlib import Path
import runpy
import sys


if __name__ == "__main__":
    backend_entry = Path(__file__).resolve().parent / "backend" / "schedule_refresh.py"
    sys.path.insert(0, str(backend_entry.parent))
    runpy.run_path(str(backend_entry), run_name="__main__")
