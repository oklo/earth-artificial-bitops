#!/usr/bin/env python3
"""Regenerate the current-day artificial bitops estimate."""

from __future__ import annotations

from pathlib import Path

from earth_bitops.current_model import run_model, write_outputs


def main() -> None:
    result = run_model(samples=300_000, seed=20260603)
    write_outputs(result, Path("data/processed"))


if __name__ == "__main__":
    main()
