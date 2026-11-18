#!/usr/bin/env python3
"""Regenerate the 2026-2035 component projection."""

from pathlib import Path

from earth_bitops.projection_model import run

if __name__ == "__main__":
    run(Path("data/processed"))
