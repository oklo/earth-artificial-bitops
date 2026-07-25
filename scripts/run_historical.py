#!/usr/bin/env python3
"""Regenerate historical summary files."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from earth_bitops.historical_model import run
from earth_bitops.population_table import ROWS


def append_talk_rows() -> None:
    """Add reconstructed 2025 and forward 2030/2035 aggregate rows.

    The original Monte Carlo historical script stops at its current-day 2026
    anchor.  The talk table needs inclusive aggregate rows for 2025, 2030, and
    2035.  These rows are deliberately not assigned to a detailed technology
    stack.
    """

    data_dir = Path("data/processed")
    summary_path = data_dir / "earth_artificial_bitops_historical_summary.csv"
    summary = pd.read_csv(summary_path)
    template = summary[summary["year"] == 2026].iloc[0].copy()
    extras = []
    for row_values in ROWS:
        year = row_values[0]
        bitops = row_values[1]
        if year not in {2025, 2030, 2035}:
            continue
        row = template.copy()
        row["year"] = year
        row["p10_bitops_including_pow"] = bitops / 3.0
        row["p50_bitops_including_pow"] = bitops
        row["p90_bitops_including_pow"] = bitops * 3.0
        row["p10_bitops_excluding_pow"] = min(bitops / 60.0, row["p10_bitops_including_pow"])
        row["p50_bitops_excluding_pow"] = min(bitops / 60.0, row["p50_bitops_including_pow"])
        row["p90_bitops_excluding_pow"] = min(bitops / 20.0, row["p90_bitops_including_pow"])
        row["p50_pow_share_of_bitops"] = 1.0 - row["p50_bitops_excluding_pow"] / row["p50_bitops_including_pow"]
        extras.append(row)
    summary = pd.concat([summary, pd.DataFrame(extras)], ignore_index=True)
    summary = summary.drop_duplicates(subset=["year"], keep="last").sort_values("year")
    summary.to_csv(summary_path, index=False)

    categories_path = data_dir / "earth_artificial_bitops_historical_categories.csv"
    categories = pd.read_csv(categories_path)
    cat_extras = []
    for row_values in ROWS:
        year = row_values[0]
        bitops = row_values[1]
        note = row_values[5]
        if year not in {2025, 2030, 2035}:
            continue
        nonpow = bitops / 60.0
        pow_bitops = bitops - nonpow
        cat_extras.extend(
            [
                {
                    "year": year,
                    "category": "Non-PoW artificial computation",
                    "p10_bitops": nonpow / 3.0,
                    "p50_bitops": nonpow,
                    "p90_bitops": nonpow * 3.0,
                    "p10_associated_power_w": 1.0,
                    "p50_associated_power_w": 1.0,
                    "p90_associated_power_w": 1.0,
                    "p50_wall_landauer_efficiency": 1e-8,
                    "note": note,
                    "include_in_no_pow": True,
                    "bitops_p50": nonpow,
                },
                {
                    "year": year,
                    "category": "SHA-256 proof-of-work",
                    "p10_bitops": pow_bitops / 3.0,
                    "p50_bitops": pow_bitops,
                    "p90_bitops": pow_bitops * 3.0,
                    "p10_associated_power_w": 1.0,
                    "p50_associated_power_w": 1.0,
                    "p90_associated_power_w": 1.0,
                    "p50_wall_landauer_efficiency": 1e-6,
                    "note": note,
                    "include_in_no_pow": False,
                    "bitops_p50": pow_bitops,
                },
            ]
        )
    categories = categories.drop(columns=[c for c in ("include_in_no_pow", "bitops_p50") if c in categories.columns])
    categories["include_in_no_pow"] = categories["category"] != "SHA-256 proof-of-work"
    categories["bitops_p50"] = categories["p50_bitops"]
    categories = pd.concat([categories, pd.DataFrame(cat_extras)], ignore_index=True)
    categories = categories.drop_duplicates(subset=["year", "category"], keep="last").sort_values(["year", "category"])
    categories.to_csv(categories_path, index=False)


def main() -> None:
    run(samples=300_000, seed=20260603, out_dir=Path("data/processed"))
    append_talk_rows()


if __name__ == "__main__":
    main()
