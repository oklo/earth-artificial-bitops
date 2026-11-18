"""Stacked contribution diagrams for the Earth artificial-computation model.

Inputs (data/processed/):
  - earth_artificial_bitops_historical_summary.csv   (Monte Carlo p50 totals)
  - earth_artificial_bitops_historical_groups.csv    (non-PoW split by display group)
  - earth_artificial_bitops_projection_2026_2035.csv (component projection)

The Landauer layers are defined as  eta_i = N_i * kT ln 2 / P_total  so the
shaded layers add exactly to the overall wall-power Landauer efficiency.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

from earth_bitops.constants import LANDAUER_J_PER_BIT_300K

PROJECTION_YEARS = (2030, 2035)
LAST_HISTORICAL_YEAR = 2026


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


def build_plot_data(summary: pd.DataFrame, groups: pd.DataFrame, projection: pd.DataFrame) -> pd.DataFrame:
    """Return one row per year with per-group bitops, totals, power and eta."""
    nonpow_groups = [g for g in GROUP_ORDER if g != "SHA-256 proof-of-work"]
    wide = groups.pivot_table(index="year", columns="group", values="p50_bitops", aggfunc="sum").fillna(0.0)
    wide = wide.reindex(columns=GROUP_ORDER, fill_value=0.0)
    s = summary.set_index("year")
    rows = []
    for year in sorted(s.index):
        row = {"year": int(year), **{g: float(wide.loc[year, g]) for g in GROUP_ORDER}}
        row["total_bitops_including_pow"] = float(s.loc[year, "p50_bitops_including_pow"])
        row["total_bitops_excluding_pow"] = float(s.loc[year, "p50_bitops_excluding_pow"])
        row["power_including_pow_w"] = float(s.loc[year, "p50_associated_power_including_pow_w"])
        row["power_excluding_pow_w"] = float(s.loc[year, "p50_associated_power_excluding_pow_w"])
        row["projected"] = False
        rows.append(row)

    base = wide.loc[LAST_HISTORICAL_YEAR, nonpow_groups].copy()
    non_ai = base.drop("AI accelerators")
    non_ai_shares = non_ai / non_ai.sum()
    proj = projection.set_index("year")
    for year in PROJECTION_YEARS:
        r = proj.loc[year]
        nonpow = float(r["p50_bitops_excluding_pow"])
        incl = float(r["p50_bitops_including_pow"])
        ai_frac = float(r["p50_bitops_ai"]) / float(r["p50_bitops_ai"] + r["p50_bitops_other"])
        row = {"year": int(year), **{g: 0.0 for g in GROUP_ORDER}}
        row["AI accelerators"] = nonpow * ai_frac
        for g, share in non_ai_shares.items():
            row[g] = nonpow * (1.0 - ai_frac) * float(share)
        row["SHA-256 proof-of-work"] = incl - nonpow
        row["total_bitops_including_pow"] = incl
        row["total_bitops_excluding_pow"] = nonpow
        row["power_including_pow_w"] = float(r["p50_power_including_pow_w"])
        row["power_excluding_pow_w"] = float(r["p50_power_excluding_pow_w"])
        row["projected"] = True
        rows.append(row)

    out = pd.DataFrame(rows).set_index("year")
    out = out.rename(columns={g: f"bitops_{g}" for g in GROUP_ORDER})
    for g in GROUP_ORDER:
        out[f"landauer_contribution_{g}"] = out[f"bitops_{g}"] * LANDAUER_J_PER_BIT_300K / out["power_including_pow_w"]
    out["wall_landauer_efficiency_including_pow"] = (
        out["total_bitops_including_pow"] * LANDAUER_J_PER_BIT_300K / out["power_including_pow_w"]
    )
    out["wall_landauer_efficiency_excluding_pow"] = (
        out["total_bitops_excluding_pow"] * LANDAUER_J_PER_BIT_300K / out["power_excluding_pow_w"]
    )
    return out


def make_stacked_plot(plot_data: pd.DataFrame, prefix: str, total_col: str, excl_col: str,
                      ylabel: str, title: str, subtitle: str, out_base: Path, start_year: int = 1945) -> None:
    data = plot_data[plot_data.index >= start_year]
    groups = [g for g in GROUP_ORDER if data[f"{prefix}{g}"].max() > 0]
    fig, ax = plt.subplots(figsize=(12, 7.5))
    x = data.index.to_numpy()
    ax.stackplot(x, [data[f"{prefix}{g}"].to_numpy() for g in groups], labels=groups, alpha=0.68)
    ax.plot(x, data[total_col].to_numpy(), color="black", linewidth=2.4, label="Overall including PoW")
    ax.plot(x, data[excl_col].to_numpy(), color="black", linewidth=1.8, linestyle="--", label="Overall excluding PoW")
    ax.axvline(LAST_HISTORICAL_YEAR, color="0.3", linewidth=1.0, linestyle=":")
    ax.text(LAST_HISTORICAL_YEAR + 0.4, 0.03, "projection", transform=ax.get_xaxis_transform(), fontsize=9, color="0.3")
    ax.set_yscale("log")
    ax.set_ylim(bottom=data[excl_col].min() * 1e-3)
    ax.set_xlim(x.min(), x.max())
    ax.set_xlabel("Year")
    ax.set_ylabel(ylabel)
    ax.set_title(f"{title}\n{subtitle}", pad=14)
    ax.grid(True, which="major", linewidth=0.5, alpha=0.35)
    ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=False)
    fig.tight_layout()
    fig.savefig(out_base.with_suffix(".png"), dpi=240, bbox_inches="tight")
    fig.savefig(out_base.with_suffix(".svg"), bbox_inches="tight")
    plt.close(fig)
