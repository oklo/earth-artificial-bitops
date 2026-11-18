#!/usr/bin/env python3
"""Regenerate stacked figures (history 1945-2026 plus 2030/2035 projection) into figures/."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from earth_bitops.plotting import build_plot_data, make_stacked_plot


def main() -> None:
    data_dir = Path("data/processed")
    figures_dir = Path("figures")
    figures_dir.mkdir(parents=True, exist_ok=True)
    plot_data = build_plot_data(
        pd.read_csv(data_dir / "earth_artificial_bitops_historical_summary.csv"),
        pd.read_csv(data_dir / "earth_artificial_bitops_historical_groups.csv"),
        pd.read_csv(data_dir / "earth_artificial_bitops_projection_2026_2035.csv"),
    )
    plot_data.to_csv(data_dir / "earth_artificial_bitops_diagram_plot_data.csv")

    make_stacked_plot(
        plot_data, "bitops_", "total_bitops_including_pow", "total_bitops_excluding_pow",
        "Functional bit operations per second",
        "Estimated growth of artificial computation on Earth",
        "Median model; shaded layers are contributing computation categories",
        figures_dir / "bitops_growth_stacked",
    )
    make_stacked_plot(
        plot_data, "landauer_contribution_", "wall_landauer_efficiency_including_pow",
        "wall_landauer_efficiency_excluding_pow",
        "Wall-power Landauer efficiency",
        "Estimated evolution of artificial-computation Landauer efficiency",
        r"Median model at 300 K; shaded layers are $N_i kT\ln2/P_{\rm total}$ contributions",
        figures_dir / "landauer_efficiency_stacked",
    )


if __name__ == "__main__":
    main()
