#!/usr/bin/env python3
"""
Generate stacked contribution diagrams for the Earth artificial-computation model.

Inputs expected in the same directory by default:
  - earth_artificial_bitops_historical_summary.csv
  - earth_artificial_bitops_historical_categories.csv

Outputs:
  - earth_artificial_bitops_growth_stacked.png/.svg
  - earth_artificial_landauer_efficiency_stacked.png/.svg
  - earth_artificial_bitops_diagram_plot_data.csv

The Landauer layers are defined as:
    eta_i = N_i * kT ln 2 / P_total
so the shaded layers add exactly to the overall wall-power Landauer efficiency.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


def group_category(name: str) -> str:
    n = name.lower().replace("‑", "-").replace("–", "-").replace("—", "-")
    if "proof-of-work" in n or "sha-256" in n or "bitcoin" in n:
        return "SHA-256 proof-of-work"
    if "ai accelerator" in n or "deep-learning" in n:
        return "AI accelerators"
    if (
        "data centre" in n or "data-center" in n or "data-centre" in n or
        "data center" in n or "cloud" in n or "server" in n or
        "mainframe" in n or "supercomputer" in n or "mini" in n
    ):
        return "Data centres / servers"
    if "embedded" in n or "application-specific" in n or "asic" in n or "control" in n:
        return "Embedded / application-specific"
    if "personal computer" in n or "workstation" in n or "console" in n:
        return "PCs / workstations / consoles"
    if "phone" in n or "tablet" in n or "wearable" in n or "mobile handset" in n or "pda" in n:
        return "Phones / tablets / wearables"
    if "telecom" in n or "data-transmission" in n or "network" in n:
        return "Telecom / networks"
    if "consumer media" in n or "camera" in n:
        return "Consumer media electronics"
    if (
        "electromechanical" in n or "punched-card" in n or "analog" in n or
        "early electronic" in n or "first-generation" in n or "commercial/scientific" in n
    ):
        return "Early / legacy computation"
    return "Other computation"


GROUP_ORDER = [
    "Early / legacy computation",
    "Embedded / application-specific",
    "Data centres / servers",
    "PCs / workstations / consoles",
    "Telecom / networks",
    "Phones / tablets / wearables",
    "Consumer media electronics",
    "AI accelerators",
    "Other computation",
    "SHA-256 proof-of-work",
]


def build_plot_data(summary: pd.DataFrame, categories: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    summary = summary.sort_values("year").reset_index(drop=True)
    categories = categories.copy()
    categories["group"] = categories["category"].map(group_category)

    years = summary["year"].to_numpy()
    summary_indexed = summary.set_index("year")

    contrib = pd.DataFrame(index=years, columns=GROUP_ORDER, dtype=float).fillna(0.0)
    eta_contrib = pd.DataFrame(index=years, columns=GROUP_ORDER, dtype=float).fillna(0.0)

    for year in years:
        total_incl = float(summary_indexed.loc[year, "p50_bitops_including_pow"])
        total_excl = float(summary_indexed.loc[year, "p50_bitops_excluding_pow"])
        eta_incl = float(summary_indexed.loc[year, "p50_wall_landauer_efficiency_including_pow"])
        pow_bitops = max(total_incl - total_excl, 0.0)

        rows = categories[(categories["year"] == year) & (categories["include_in_no_pow"].astype(bool))]
        grouped_nonpow = rows.groupby("group")["bitops_p50"].sum()

        if grouped_nonpow.sum() > 0:
            nonpow_alloc = grouped_nonpow / grouped_nonpow.sum() * total_excl
        else:
            nonpow_alloc = pd.Series(dtype=float)

        for group in GROUP_ORDER:
            if group == "SHA-256 proof-of-work":
                value = pow_bitops
            else:
                value = float(nonpow_alloc.get(group, 0.0))
            contrib.loc[year, group] = value
            eta_contrib.loc[year, group] = eta_incl * value / total_incl if total_incl > 0 else 0.0

    return summary_indexed, contrib, eta_contrib


def make_stacked_plot(
    values_df: pd.DataFrame,
    total_series: pd.Series,
    excl_series: pd.Series,
    ylabel: str,
    title: str,
    subtitle: str,
    out_base: Path,
) -> None:
    fig, ax = plt.subplots(figsize=(12, 7.5))
    x = values_df.index.to_numpy()
    layers = [values_df[group].to_numpy() for group in GROUP_ORDER]

    ax.stackplot(x, layers, labels=GROUP_ORDER, alpha=0.68)
    ax.plot(x, total_series.loc[x].to_numpy(), linewidth=2.8, label="Overall including PoW")
    ax.plot(x, excl_series.loc[x].to_numpy(), linewidth=2.4, linestyle="--", label="Overall excluding PoW")

    ax.set_yscale("log")
    ax.set_xlim(x.min(), x.max())
    ax.set_xlabel("Year")
    ax.set_ylabel(ylabel)
    ax.set_title(f"{title}\n{subtitle}", pad=14)
    ax.grid(True, which="both", linewidth=0.5, alpha=0.35)
    ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=False)

    fig.tight_layout()
    fig.savefig(out_base.with_suffix(".png"), dpi=240, bbox_inches="tight")
    fig.savefig(out_base.with_suffix(".svg"), bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=Path("."))
    args = parser.parse_args()

    summary = pd.read_csv(args.data_dir / "earth_artificial_bitops_historical_summary.csv")
    categories = pd.read_csv(args.data_dir / "earth_artificial_bitops_historical_categories.csv")

    summary_indexed, contrib, eta_contrib = build_plot_data(summary, categories)

    plot_data = contrib.copy()
    plot_data.columns = [f"bitops_{c}" for c in plot_data.columns]
    for col in eta_contrib.columns:
        plot_data[f"landauer_contribution_{col}"] = eta_contrib[col]
    plot_data["total_bitops_including_pow"] = summary_indexed["p50_bitops_including_pow"]
    plot_data["total_bitops_excluding_pow"] = summary_indexed["p50_bitops_excluding_pow"]
    plot_data["wall_landauer_efficiency_including_pow"] = summary_indexed["p50_wall_landauer_efficiency_including_pow"]
    plot_data["wall_landauer_efficiency_excluding_pow"] = summary_indexed["p50_wall_landauer_efficiency_excluding_pow"]
    plot_data.to_csv(args.data_dir / "earth_artificial_bitops_diagram_plot_data.csv", index_label="year")

    make_stacked_plot(
        contrib,
        summary_indexed["p50_bitops_including_pow"],
        summary_indexed["p50_bitops_excluding_pow"],
        "Functional bit operations per second",
        "Estimated growth of artificial computation on Earth",
        "Median model; shaded layers are contributing computation categories",
        args.data_dir / "earth_artificial_bitops_growth_stacked",
    )

    make_stacked_plot(
        eta_contrib,
        summary_indexed["p50_wall_landauer_efficiency_including_pow"],
        summary_indexed["p50_wall_landauer_efficiency_excluding_pow"],
        "Wall-power Landauer efficiency",
        "Estimated evolution of artificial-computation Landauer efficiency",
        r"Median model at 300 K; shaded layers are $N_i kT\ln2/P_{\rm total}$ contributions",
        args.data_dir / "earth_artificial_landauer_efficiency_stacked",
    )


if __name__ == "__main__":
    main()
