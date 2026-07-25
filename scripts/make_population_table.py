#!/usr/bin/env python3
"""Regenerate the talk-facing population table."""

from pathlib import Path

from earth_bitops.population_table import write_table


if __name__ == "__main__":
    write_table(Path("data/processed"), Path("figures"))
