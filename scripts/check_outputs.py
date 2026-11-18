#!/usr/bin/env python3
"""Consistency checks for generated artifacts.

These test relationships between outputs (energy equation, sums, monotonicity,
cross-file agreement) rather than comparing outputs with hard-coded copies of
themselves.
"""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

from earth_bitops.constants import LANDAUER_J_PER_BIT_300K as E_L, THRESHOLDS

DATA = Path("data/processed")
FIGURES = Path("figures")


def close(a: float, b: float, rel: float, what: str) -> None:
    if not math.isclose(a, b, rel_tol=rel):
        raise AssertionError(f"{what}: {a:g} vs {b:g} (tolerance {rel:.0%})")


def main() -> None:
    current = pd.read_json(DATA / "earth_artificial_bitops_current_estimate.json", typ="series")
    hist = pd.read_csv(DATA / "earth_artificial_bitops_historical_summary.csv").set_index("year")
    groups = pd.read_csv(DATA / "earth_artificial_bitops_historical_groups.csv")
    proj = pd.read_csv(DATA / "earth_artificial_bitops_projection_2026_2035.csv").set_index("year")
    plot = pd.read_csv(DATA / "earth_artificial_bitops_diagram_plot_data.csv").set_index("year")
    cross = pd.read_csv(DATA / "earth_artificial_bitops_future_threshold_crossings.csv")
    table = pd.read_csv(DATA / "earth_artificial_bitops_population_table.csv").set_index("year")

    # 1. Historical model: every year is a model row; series are positive and monotone in the medians.
    assert list(hist.index) == sorted(hist.index) and {1945, 2025, 2026} <= set(hist.index)
    assert set(hist.index).isdisjoint({2030, 2035}), "forward years must not be appended to the historical file"
    n = hist["p50_bitops_excluding_pow"]
    assert (n.diff().dropna() > 0).all(), "non-PoW bitops must increase"
    for tag in ("including_pow", "excluding_pow"):
        eta = hist[f"p50_wall_landauer_efficiency_{tag}"]
        assert ((eta > 0) & (eta < 1e-2)).all(), "historical eta_L must be far below any irreversible ceiling"
        implied = hist[f"p50_bitops_{tag}"] * E_L / hist[f"p50_associated_power_{tag}_w"]
        for y in hist.index:  # median of ratio vs ratio of medians; equal up to Monte Carlo/skew effects
            close(float(eta[y]), float(implied[y]), 0.25, f"energy equation {tag} {y}")

    # 2. Current-day model and historical 2026 anchor agree.
    close(float(hist.loc[2026, "p50_bitops_excluding_pow"]), float(current["total_excluding_pow"]["p50"]), 0.10,
          "2026 non-PoW: historical anchor vs current model")
    close(float(hist.loc[2026, "p50_bitops_including_pow"]), float(current["total_including_pow"]["p50"]), 0.15,
          "2026 inclusive: historical vs current model")

    # 3. Group table sums to the totals.
    for y, g in groups.groupby("year"):
        close(float(g["p50_bitops"].sum()), float(hist.loc[y, "p50_bitops_including_pow"]), 1e-9, f"group sum {y}")

    # 4. Projection starts at the historical 2026 row and stays physically plausible.
    close(float(proj.loc[2026, "p50_bitops_including_pow"]), float(hist.loc[2026, "p50_bitops_including_pow"]), 0.05,
          "projection 2026 vs history (inclusive bitops)")
    close(float(proj.loc[2026, "p50_power_including_pow_w"]), float(hist.loc[2026, "p50_associated_power_including_pow_w"]),
          0.05, "projection 2026 vs history (power)")
    assert (proj.filter(like="p90_eta") < 1e-2).all().all(), "projected eta_L must stay below the irreversible ceiling"
    assert (proj["p50_power_including_pow_w"].diff().dropna() > 0).all()
    assert (proj["p10_bitops_including_pow"] <= proj["p50_bitops_including_pow"]).all()

    # 5. Plot data: layers add up; eta columns satisfy the energy equation exactly.
    bit_cols = [c for c in plot.columns if c.startswith("bitops_")]
    for y, r in plot.iterrows():
        close(float(r[bit_cols].sum()), float(r["total_bitops_including_pow"]), 1e-9, f"stack sum {y}")
        close(float(r["wall_landauer_efficiency_including_pow"]),
              float(r["total_bitops_including_pow"]) * E_L / float(r["power_including_pow_w"]), 1e-9, f"plot eta {y}")

    # 6. Talk table agrees with its sources and with the energy equation.
    for y, r in table.iterrows():
        src = float(proj.loc[y, "p50_bitops_including_pow"]) if y > 2026 else float(hist.loc[y, "p50_bitops_including_pow"])
        close(float(r["bitops_per_s_including_pow"]), src, 1e-9, f"table bitops {y}")
        close(float(r["landauer_efficiency_including_pow"]),
              float(r["bitops_per_s_including_pow"]) * E_L / float(r["power_w_including_pow"]), 1e-9, f"table eta {y}")
        close(float(r["bitops_per_erg_including_pow"]) * 1e7 * E_L, float(r["landauer_efficiency_including_pow"]), 1e-9,
              f"table bitops/erg {y}")
    assert table.index.min() == 1945
    assert (table.loc[[2030, 2035], "basis"].str.startswith("projection")).all()

    # 7. Future crossings: ordered in threshold size; respond to assumptions in the right direction.
    order = sorted(THRESHOLDS, key=THRESHOLDS.get)
    for _, r in cross.iterrows():
        years = [r[k] for k in order]
        assert all(a <= b for a, b in zip(years, years[1:])), f"crossings not ordered: {r.to_dict()}"
    irr = cross[cross["family"] == "irreversible"]
    for _, g in irr.groupby("trend_window"):
        g = g.sort_values("eta_max")
        for k in order:
            assert g[k].is_monotonic_increasing, "a higher eta ceiling must not make a crossing earlier"
    sens = cross[cross["family"] == "demand_sensitivity"]
    for _, g in sens.groupby("eta_max"):
        g = g.sort_values("g_bitops")
        for k in order:
            assert g[k].is_monotonic_decreasing, "faster demand growth must not make a crossing later"
    for w, g in cross[cross["family"] != "demand_sensitivity"].groupby("trend_window"):
        rev = g[g["family"] == "power_trend_requires_reversible"].iloc[0]
        lim = g[(g["family"] == "irreversible") & (g["eta_max"] == 1.0)].iloc[0]
        for k in order:
            assert rev[k] >= lim[k], "the power-trend path cannot cross before the Landauer-limited path"

    for name in ("bitops_growth_stacked.png", "bitops_growth_stacked.svg", "landauer_efficiency_stacked.png",
                 "landauer_efficiency_stacked.svg", "future_power_projection.png", "future_eta_projection.png",
                 "future_bitops_projection.png", "constant_growth_sensitivity.png", "constant_growth_sensitivity.svg",
                 "population_table_zoom_readable.png", "population_table_zoom_readable.svg"):
        path = FIGURES / name
        if not path.exists() or path.stat().st_size == 0:
            raise AssertionError(f"missing or empty artifact: {path}")
    print("All output checks passed.")


if __name__ == "__main__":
    main()
