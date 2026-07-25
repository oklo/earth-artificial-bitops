"""Future bitops and energy-threshold sensitivity models.

The future calculations are deliberately compact reconstructions of the
talk-model outputs.  They are sensitivity analyses, not forecasts.
"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from earth_bitops.constants import (
    CURRENT_GLOBAL_PRIMARY_ENERGY_W,
    CURRENT_INCLUSIVE_BITOPS_PER_S,
    CURRENT_INCLUSIVE_LANDAUER_EFFICIENCY,
    CURRENT_INCLUSIVE_POWER_W,
    EARTH_INTERCEPTED_SOLAR_W,
    LANDAUER_J_PER_BIT_300K,
    SOLAR_LUMINOSITY_W,
)


BASE_YEAR = 2026
END_YEAR = 2500
THRESHOLDS = {
    "current_global_primary_energy": CURRENT_GLOBAL_PRIMARY_ENERGY_W,
    "earth_intercepted_solar_power": EARTH_INTERCEPTED_SOLAR_W,
    "solar_luminosity": SOLAR_LUMINOSITY_W,
}


@dataclass(frozen=True)
class Scenario:
    name: str
    anchor_years: tuple[int, ...]
    anchor_powers_w: tuple[float, ...]
    anchor_eta: tuple[float, ...]
    note: str


CENTRAL_SCENARIO = Scenario(
    name="central_declining_growth",
    anchor_years=(BASE_YEAR, 2090, 2170, 2473, END_YEAR),
    anchor_powers_w=(
        CURRENT_INCLUSIVE_POWER_W,
        CURRENT_GLOBAL_PRIMARY_ENERGY_W,
        EARTH_INTERCEPTED_SOLAR_W,
        SOLAR_LUMINOSITY_W,
        SOLAR_LUMINOSITY_W * 4.0,
    ),
    anchor_eta=(CURRENT_INCLUSIVE_LANDAUER_EFFICIENCY, 4.5e-4, 2.5e-3, 0.25, 0.30),
    note="Calibrated to previous central declining-growth threshold crossings.",
)


def _constant_growth_eta_anchor(year: int, power_w: float, growth_rate: float) -> float:
    bitops = CURRENT_INCLUSIVE_BITOPS_PER_S * (1.0 + growth_rate) ** (year - BASE_YEAR)
    eta = bitops * LANDAUER_J_PER_BIT_300K / power_w
    return min(eta, 1.0)


CONSTANT_50_SCENARIO = Scenario(
    name="constant_50pct_bitops_growth",
    anchor_years=(BASE_YEAR, 2065, 2089, 2142, 2160, END_YEAR),
    anchor_powers_w=(
        CURRENT_INCLUSIVE_POWER_W,
        CURRENT_GLOBAL_PRIMARY_ENERGY_W,
        EARTH_INTERCEPTED_SOLAR_W,
        SOLAR_LUMINOSITY_W,
        SOLAR_LUMINOSITY_W * (1.5 ** (2160 - 2142)),
        SOLAR_LUMINOSITY_W * (1.5 ** (END_YEAR - 2142)),
    ),
    anchor_eta=(
        CURRENT_INCLUSIVE_LANDAUER_EFFICIENCY,
        _constant_growth_eta_anchor(2065, CURRENT_GLOBAL_PRIMARY_ENERGY_W, 0.50),
        _constant_growth_eta_anchor(2089, EARTH_INTERCEPTED_SOLAR_W, 0.50),
        _constant_growth_eta_anchor(2142, SOLAR_LUMINOSITY_W, 0.50),
        1.0,
        1.0,
    ),
    note="50%/yr bitops demand growth with efficiency improving toward the Landauer limit.",
)


def interpolate_log(years: np.ndarray, anchor_years: tuple[int, ...], anchor_values: tuple[float, ...]) -> np.ndarray:
    return np.exp(np.interp(years, np.asarray(anchor_years), np.log(np.asarray(anchor_values))))


def scenario_timeseries(scenario: Scenario, growth_rate: float | None = None) -> list[dict[str, float | int | str]]:
    years = np.arange(BASE_YEAR, END_YEAR + 1)
    eta = interpolate_log(years, scenario.anchor_years, scenario.anchor_eta)
    if growth_rate is None:
        power = interpolate_log(years, scenario.anchor_years, scenario.anchor_powers_w)
        bitops = power * eta / LANDAUER_J_PER_BIT_300K
    else:
        bitops = CURRENT_INCLUSIVE_BITOPS_PER_S * (1.0 + growth_rate) ** (years - BASE_YEAR)
        power = bitops * LANDAUER_J_PER_BIT_300K / eta

    return [
        {
            "year": int(year),
            "scenario": scenario.name,
            "bitops_per_s": float(n),
            "landauer_efficiency": float(e),
            "power_w": float(p),
        }
        for year, n, e, p in zip(years, bitops, eta, power, strict=True)
    ]


def crossing_year(rows: list[dict[str, float | int | str]], threshold_w: float) -> int:
    for row in rows:
        if float(row["power_w"]) >= threshold_w * (1.0 - 1e-12):
            return int(row["year"])
    raise ValueError(f"threshold not crossed: {threshold_w:g} W")


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def make_projection_plot(rows: list[dict[str, float | int | str]], y_key: str, ylabel: str, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 6))
    for scenario in sorted({str(r["scenario"]) for r in rows}):
        subset = [r for r in rows if r["scenario"] == scenario]
        ax.plot([r["year"] for r in subset], [r[y_key] for r in subset], label=scenario.replace("_", " "))
    if y_key == "power_w":
        for label, value in THRESHOLDS.items():
            ax.axhline(value, linewidth=1.1, linestyle="--", alpha=0.65, label=label.replace("_", " "))
    ax.set_yscale("log")
    ax.set_xlabel("Year")
    ax.set_ylabel(ylabel)
    ax.grid(True, which="both", linewidth=0.45, alpha=0.35)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=220)
    plt.close(fig)


def make_constant_sensitivity_plot(rows: list[dict[str, float | int | str]], png_path: Path, svg_path: Path) -> None:
    subset = [r for r in rows if r["scenario"] == CONSTANT_50_SCENARIO.name]
    years = [r["year"] for r in subset]
    power = [r["power_w"] for r in subset]
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(years, power, color="#8646c8", linewidth=2.3, label="50%/yr bitops demand")
    for label, value in THRESHOLDS.items():
        ax.axhline(value, linewidth=1.1, linestyle="--", alpha=0.7, label=label.replace("_", " "))
    ax.set_yscale("log")
    ax.set_xlabel("Year")
    ax.set_ylabel("Power required for irreversible bit operations (W)")
    ax.set_title("Constant-growth sensitivity")
    ax.grid(True, which="both", linewidth=0.45, alpha=0.35)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(png_path, dpi=220)
    fig.savefig(svg_path)
    plt.close(fig)


def run(out_data: Path, out_figures: Path) -> dict[str, int]:
    central = scenario_timeseries(CENTRAL_SCENARIO)
    constant = scenario_timeseries(CONSTANT_50_SCENARIO, growth_rate=0.50)
    all_rows = central + constant

    write_csv(out_data / "earth_artificial_bitops_future_timeseries_central.csv", central)
    write_csv(out_data / "earth_artificial_bitops_future_timeseries_constant_50pct.csv", constant)

    crossing_rows = []
    for scenario_name, rows in ((CENTRAL_SCENARIO.name, central), (CONSTANT_50_SCENARIO.name, constant)):
        for threshold_name, threshold_w in THRESHOLDS.items():
            crossing_rows.append(
                {
                    "scenario": scenario_name,
                    "threshold": threshold_name,
                    "threshold_w": threshold_w,
                    "crossing_year": crossing_year(rows, threshold_w),
                }
            )
    write_csv(out_data / "earth_artificial_bitops_future_threshold_crossings.csv", crossing_rows)

    summary_rows = [
        {
            "scenario": CENTRAL_SCENARIO.name,
            "description": CENTRAL_SCENARIO.note,
            "global_energy_crossing_year": crossing_year(central, CURRENT_GLOBAL_PRIMARY_ENERGY_W),
            "earth_solar_crossing_year": crossing_year(central, EARTH_INTERCEPTED_SOLAR_W),
            "solar_luminosity_crossing_year": crossing_year(central, SOLAR_LUMINOSITY_W),
        },
        {
            "scenario": CONSTANT_50_SCENARIO.name,
            "description": CONSTANT_50_SCENARIO.note,
            "global_energy_crossing_year": crossing_year(constant, CURRENT_GLOBAL_PRIMARY_ENERGY_W),
            "earth_solar_crossing_year": crossing_year(constant, EARTH_INTERCEPTED_SOLAR_W),
            "solar_luminosity_crossing_year": crossing_year(constant, SOLAR_LUMINOSITY_W),
        },
    ]
    write_csv(out_data / "earth_artificial_bitops_future_projection_summary.csv", summary_rows)

    out_figures.mkdir(parents=True, exist_ok=True)
    make_projection_plot(all_rows, "power_w", "Power required (W)", out_figures / "future_power_projection.png")
    make_projection_plot(all_rows, "landauer_efficiency", "Landauer efficiency", out_figures / "future_eta_projection.png")
    make_projection_plot(all_rows, "bitops_per_s", "Functional bit operations per second", out_figures / "future_bitops_projection.png")
    make_constant_sensitivity_plot(
        all_rows,
        out_figures / "constant_growth_sensitivity.png",
        out_figures / "constant_growth_sensitivity.svg",
    )
    (out_data / "earth_artificial_bitops_future_summary.md").write_text(
        "# Future projection summary\n\n"
        "These are sensitivity calculations, not forecasts.  They preserve the threshold-crossing "
        "years used in the talk model while making the energy equation explicit.\n\n"
        "- Central declining-growth model: global energy ~2090, Earth-intercepted solar power ~2170, "
        "solar luminosity ~2473.\n"
        "- Constant 50%/yr bitops-demand sensitivity: global energy ~2065, Earth-intercepted solar "
        "power ~2089, solar luminosity ~2142.\n",
        encoding="utf-8",
    )
    return {row["scenario"] + ":" + row["threshold"]: int(row["crossing_year"]) for row in crossing_rows}
