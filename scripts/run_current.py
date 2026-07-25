#!/usr/bin/env python3
"""Regenerate the current-day artificial bitops estimate."""

from __future__ import annotations

from pathlib import Path

from earth_bitops.current_model import run_model, write_outputs
from earth_bitops.constants import (
    CURRENT_INCLUSIVE_BITOPS_PER_S,
    CURRENT_INCLUSIVE_LANDAUER_EFFICIENCY,
    CURRENT_INCLUSIVE_POWER_W,
    CURRENT_NON_POW_BITOPS_PER_S,
    CURRENT_NON_POW_LANDAUER_EFFICIENCY,
    LANDAUER_J_PER_BIT_300K,
)


def main() -> None:
    out_dir = Path("data/processed")
    result = run_model(samples=300_000, seed=20260603)
    write_outputs(result, out_dir)
    (out_dir / "earth_artificial_bitops_landauer_summary.csv").write_text(
        "case,bitops_per_s,associated_power_w,landauer_efficiency,landauer_j_per_bit_300k\n"
        f"including_pow,{CURRENT_INCLUSIVE_BITOPS_PER_S},{CURRENT_INCLUSIVE_POWER_W},"
        f"{CURRENT_INCLUSIVE_LANDAUER_EFFICIENCY},{LANDAUER_J_PER_BIT_300K}\n"
        f"excluding_pow,{CURRENT_NON_POW_BITOPS_PER_S},"
        f"{CURRENT_NON_POW_BITOPS_PER_S * LANDAUER_J_PER_BIT_300K / CURRENT_NON_POW_LANDAUER_EFFICIENCY},"
        f"{CURRENT_NON_POW_LANDAUER_EFFICIENCY},{LANDAUER_J_PER_BIT_300K}\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
