"""Backward-compatible entry point. Use `python -m pppt.cli` for the package version."""
import sys
import os

# Add src/ to path so the pppt package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from pppt.cli import main

if __name__ == "__main__":
    main()
