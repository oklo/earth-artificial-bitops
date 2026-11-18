#!/usr/bin/env python3
"""Regenerate historical summary files (1940-2026, including 1945 and 2025).

Every row is produced by the Monte Carlo historical model.  Forward years are
handled separately by scripts/run_projection.py; nothing is hand-appended.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from earth_bitops.constants import LANDAUER_J_PER_BIT_300K
from earth_bitops.historical_model import run

DATA = Path("data/processed")
SHARES = Path("data/reference/historical_nonpow_group_shares.csv")


def write_group_table(summary: pd.DataFrame) -> None:
    """Allocate non-PoW p50 bitops to display groups using reference shares."""
    shares = pd.read_csv(SHARES)
    rows = []
    for _, s in summary.iterrows():
        year = int(s["year"])
        nonpow = float(s["p50_bitops_excluding_pow"])
        incl = float(s["p50_bitops_including_pow"])
        for _, sh in shares[shares["year"] == year].iterrows():
            rows.append({"year": year, "group": sh["group"],
                         "p50_bitops": nonpow * float(sh["share_of_nonpow_bitops"])})
        rows.append({"year": year, "group": "SHA-256 proof-of-work", "p50_bitops": max(incl - nonpow, 0.0)})
    out = pd.DataFrame(rows)
    out["share_of_bitops_including_pow"] = out["p50_bitops"] / out.groupby("year")["p50_bitops"].transform("sum")
    out.to_csv(DATA / "earth_artificial_bitops_historical_groups.csv", index=False)


def write_landauer_summary(summary: pd.DataFrame) -> None:
    s = summary[summary["year"] == 2026].iloc[0]
    rows = []
    for case, tag in (("including_pow", "including_pow"), ("excluding_pow", "excluding_pow")):
        rows.append({
            "case": case,
            "bitops_per_s": s[f"p50_bitops_{tag}"],
            "associated_power_w": s[f"p50_associated_power_{tag}_w"],
            "landauer_efficiency": s[f"p50_wall_landauer_efficiency_{tag}"],
            "landauer_j_per_bit_300k": LANDAUER_J_PER_BIT_300K,
        })
    pd.DataFrame(rows).to_csv(DATA / "earth_artificial_bitops_landauer_summary.csv", index=False)


def main() -> None:
    run(samples=300_000, seed=20260603, out_dir=DATA)
    path = DATA / "earth_artificial_bitops_historical_summary.csv"
    summary = pd.read_csv(path).sort_values("year")
    summary.to_csv(path, index=False)
    cats = DATA / "earth_artificial_bitops_historical_categories.csv"
    pd.read_csv(cats).sort_values(["year", "category"]).to_csv(cats, index=False)
    write_group_table(summary)
    write_landauer_summary(summary)


if __name__ == "__main__":
    main()
