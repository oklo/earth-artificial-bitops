#!/usr/bin/env python3
"""Basic output validation for the repository artifacts."""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd


def approx(value: float, target: float, rel: float) -> None:
    if not math.isclose(value, target, rel_tol=rel):
        raise AssertionError(f"{value:g} not within {rel:.1%} of {target:g}")


def main() -> None:
    data = Path("data/processed")
    figures = Path("figures")
    current = pd.read_csv(data / "earth_artificial_bitops_current_estimate.csv")
    summary = pd.read_csv(data / "earth_artificial_bitops_historical_summary.csv")
    plot = pd.read_csv(data / "earth_artificial_bitops_diagram_plot_data.csv")
    crossings = pd.read_csv(data / "earth_artificial_bitops_future_threshold_crossings.csv")
    table = pd.read_csv(data / "earth_artificial_bitops_population_table.csv")

    assert (summary.filter(like="bitops").select_dtypes("number") >= 0).all().all()
    eta_cols = [c for c in summary.columns if "landauer_efficiency" in c]
    assert (summary[eta_cols] > 0).all().all()
    assert (summary[eta_cols] < 1).all().all()
    approx(float(summary.loc[summary["year"] == 2026, "p50_bitops_including_pow"].iloc[0]), 1.0e26, 0.15)
    approx(float(summary.loc[summary["year"] == 2026, "p50_bitops_excluding_pow"].iloc[0]), 1.0e24, 0.50)
    approx(float(summary.loc[summary["year"] == 2026, "p50_wall_landauer_efficiency_including_pow"].iloc[0]), 1.6e-6, 0.15)
    approx(float(summary.loc[summary["year"] == 2026, "p50_wall_landauer_efficiency_excluding_pow"].iloc[0]), 2.4e-8, 0.50)

    for year, target in {1940: 3.9e6, 1950: 3.0e8, 1960: 3.0e10, 1970: 3.0e12, 1980: 3.0e14, 1990: 3.0e16, 1995: 5.0e17, 2000: 1.1e19, 2005: 3.0e20, 2010: 2.5e21, 2015: 7.3e22, 2020: 1.3e25, 2025: 7.9e25, 2030: 1.9e27, 2035: 4.5e28}.items():
        value = float(summary.loc[summary["year"] == year, "p50_bitops_including_pow"].iloc[0])
        approx(value, target, 0.12)

    bitop_cols = [c for c in plot.columns if c.startswith("bitops_")]
    assert all(
        math.isclose(row[bitop_cols].sum(), row["total_bitops_including_pow"], rel_tol=1e-9)
        for _, row in plot.iterrows()
    )
    assert "Extrapolated" not in table.loc[table["year"] == 2025, "primary_contributors"].iloc[0]
    assert "Extrapolated" in table.loc[table["year"] == 2030, "primary_contributors"].iloc[0]
    assert "Extrapolated" in table.loc[table["year"] == 2035, "primary_contributors"].iloc[0]
    for column in (
        "average_landauer_efficiency",
        "bitops_per_person_per_year",
        "energy_per_person_per_year",
        "primary_contributors",
    ):
        assert column in table.columns

    expected_crossings = {
        ("central_declining_growth", "current_global_primary_energy"): 2090,
        ("central_declining_growth", "earth_intercepted_solar_power"): 2170,
        ("central_declining_growth", "solar_luminosity"): 2473,
        ("constant_50pct_bitops_growth", "current_global_primary_energy"): 2065,
        ("constant_50pct_bitops_growth", "earth_intercepted_solar_power"): 2089,
        ("constant_50pct_bitops_growth", "solar_luminosity"): 2142,
    }
    for key, year in expected_crossings.items():
        row = crossings[(crossings["scenario"] == key[0]) & (crossings["threshold"] == key[1])]
        assert int(row["crossing_year"].iloc[0]) == year

    for path in [
        figures / "bitops_growth_stacked.png",
        figures / "bitops_growth_stacked.svg",
        figures / "landauer_efficiency_stacked.png",
        figures / "landauer_efficiency_stacked.svg",
        figures / "future_power_projection.png",
        figures / "future_eta_projection.png",
        figures / "future_bitops_projection.png",
        figures / "constant_growth_sensitivity.png",
        figures / "constant_growth_sensitivity.svg",
        figures / "population_table_zoom_readable.png",
        figures / "population_table_zoom_readable.svg",
    ]:
        if not path.exists() or path.stat().st_size == 0:
            raise AssertionError(f"missing or empty artifact: {path}")

    assert not current.empty
    print("All output checks passed.")


if __name__ == "__main__":
    main()
