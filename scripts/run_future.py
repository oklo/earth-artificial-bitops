#!/usr/bin/env python3
"""Regenerate future projection data and figures."""

from pathlib import Path

from earth_bitops.future_model import run


if __name__ == "__main__":
    run(Path("data/processed"), Path("figures"))
