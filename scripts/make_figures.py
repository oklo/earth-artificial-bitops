#!/usr/bin/env python3
"""Regenerate historical stacked figures into figures/."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from earth_bitops.plotting import build_plot_data, make_stacked_plot


def main() -> None:
    data_dir = Path("data/processed")
    figures_dir = Path("figures")
    figures_dir.mkdir(parents=True, exist_ok=True)
    summary = pd.read_csv(data_dir / "earth_artificial_bitops_historical_summary.csv")
    categories = pd.read_csv(data_dir / "earth_artificial_bitops_historical_categories.csv")
    if "bitops_p50" not in categories.columns:
        categories["bitops_p50"] = categories["p50_bitops"]
    if "include_in_no_pow" not in categories.columns:
        categories["include_in_no_pow"] = categories["category"] != "SHA-256 proof-of-work"

    summary_indexed, contrib, eta_contrib = build_plot_data(summary, categories)
    plot_data = contrib.copy()
    plot_data.columns = [f"bitops_{c}" for c in plot_data.columns]
    for col in eta_contrib.columns:
        plot_data[f"landauer_contribution_{col}"] = eta_contrib[col]
    plot_data["total_bitops_including_pow"] = summary_indexed["p50_bitops_including_pow"]
    plot_data["total_bitops_excluding_pow"] = summary_indexed["p50_bitops_excluding_pow"]
    plot_data["wall_landauer_efficiency_including_pow"] = summary_indexed["p50_wall_landauer_efficiency_including_pow"]
    plot_data["wall_landauer_efficiency_excluding_pow"] = summary_indexed["p50_wall_landauer_efficiency_excluding_pow"]
    plot_data.to_csv(data_dir / "earth_artificial_bitops_diagram_plot_data.csv", index_label="year")

    make_stacked_plot(
        contrib,
        summary_indexed["p50_bitops_including_pow"],
        summary_indexed["p50_bitops_excluding_pow"],
        "Functional bit operations per second",
        "Estimated growth of artificial computation on Earth",
        "Median model; shaded layers are contributing computation categories",
        figures_dir / "bitops_growth_stacked",
    )
    make_stacked_plot(
        eta_contrib,
        summary_indexed["p50_wall_landauer_efficiency_including_pow"],
        summary_indexed["p50_wall_landauer_efficiency_excluding_pow"],
        "Wall-power Landauer efficiency",
        "Estimated evolution of artificial-computation Landauer efficiency",
        r"Median model at 300 K; shaded layers are $N_i kT\ln2/P_{\rm total}$ contributions",
        figures_dir / "landauer_efficiency_stacked",
    )


if __name__ == "__main__":
    main()
