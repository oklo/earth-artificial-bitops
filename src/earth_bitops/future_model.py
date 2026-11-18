"""Long-run energy extrapolation: when does computation become energy-dominant?

Nothing in this module is anchored to a target year.  The inputs are:

  * the non-PoW historical series produced by the historical model, from which
    log-linear trends in bitops/s (g_N), wall power (g_P) and Landauer
    efficiency (g_eta = g_N / g_P) are fitted by least squares;
  * a ceiling eta_max on the Landauer efficiency of *irreversible* computing;
  * SHA-256 proof-of-work held at its 2026 bitops and power (it is a one-off
    component with an economically capped budget, and is negligible later).

Energy equation:   P(t) = N(t) k T ln2 / eta(t)  (+ constant PoW power)

Scenario families
-----------------
irreversible   Demand N keeps its trend.  eta keeps its trend until it reaches
               eta_max, then stays there, so power growth jumps from g_P to g_N.
               eta_max = 1 is the Landauer limit itself and gives the *latest
               possible* crossing for that demand trend.
power_trend    Power keeps its historical trend g_P forever.  This requires
               eta to keep improving past eta_max, i.e. it is only reachable
               with reversible (sub-kT ln2 per bitop) computing.
"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from earth_bitops.constants import (
    CURRENT_GLOBAL_PRIMARY_ENERGY_W,
    GLOBAL_PRIMARY_ENERGY_GROWTH,
    LANDAUER_J_PER_BIT_300K,
    THRESHOLDS,
)

BASE_YEAR = 2026
END_YEAR = 2700
FIT_WINDOWS = {"long_run_1945_2026": (1945, 2026), "modern_2000_2026": (2000, 2026)}
ETA_CEILINGS = (1e-3, 1e-2, 1.0)
HEADLINE_WINDOW = "long_run_1945_2026"
HEADLINE_ETA_MAX = 1e-2
DEMAND_SENSITIVITY = (0.20, 0.30, 0.50)
TABLE_YEARS = (2026, 2030, 2040, 2050, 2060, 2070, 2080, 2090, 2100, 2125, 2150)


@dataclass(frozen=True)
class Baseline:
    nonpow_bitops: float
    nonpow_power_w: float
    pow_bitops: float
    pow_power_w: float

    @property
    def nonpow_eta(self) -> float:
        return self.nonpow_bitops * LANDAUER_J_PER_BIT_300K / self.nonpow_power_w


@dataclass(frozen=True)
class Trend:
    window: str
    g_bitops: float   # fractional growth per year
    g_power: float

    @property
    def g_eta(self) -> float:
        return (1.0 + self.g_bitops) / (1.0 + self.g_power) - 1.0


def load_history(data_dir: Path) -> pd.DataFrame:
    return pd.read_csv(data_dir / "earth_artificial_bitops_historical_summary.csv").sort_values("year")


def baseline_from_history(hist: pd.DataFrame) -> Baseline:
    r = hist[hist["year"] == BASE_YEAR].iloc[0]
    return Baseline(
        nonpow_bitops=float(r["p50_bitops_excluding_pow"]),
        nonpow_power_w=float(r["p50_associated_power_excluding_pow_w"]),
        pow_bitops=float(r["p50_bitops_including_pow"] - r["p50_bitops_excluding_pow"]),
        pow_power_w=float(r["p50_associated_power_including_pow_w"] - r["p50_associated_power_excluding_pow_w"]),
    )


def fit_trends(hist: pd.DataFrame) -> dict[str, Trend]:
    out = {}
    for name, (lo, hi) in FIT_WINDOWS.items():
        h = hist[(hist["year"] >= lo) & (hist["year"] <= hi)]
        years = h["year"].to_numpy(dtype=float)
        slope_n = np.polyfit(years, np.log(h["p50_bitops_excluding_pow"].to_numpy()), 1)[0]
        slope_p = np.polyfit(years, np.log(h["p50_associated_power_excluding_pow_w"].to_numpy()), 1)[0]
        out[name] = Trend(name, math.exp(slope_n) - 1.0, math.exp(slope_p) - 1.0)
    return out


def path(base: Baseline, g_bitops: float, g_eta: float, eta_max: float | None, g_power: float | None = None) -> pd.DataFrame:
    """Annual path.  eta_max=None with g_power set gives the power-trend family."""
    years = np.arange(BASE_YEAR, END_YEAR + 1)
    t = (years - BASE_YEAR).astype(float)
    with np.errstate(over="ignore"):
        n_nonpow = base.nonpow_bitops * np.exp(t * math.log1p(g_bitops))
        if eta_max is None:
            p_nonpow = base.nonpow_power_w * np.exp(t * math.log1p(g_power))
            eta = n_nonpow * LANDAUER_J_PER_BIT_300K / p_nonpow
        else:
            eta = np.minimum(base.nonpow_eta * np.exp(t * math.log1p(g_eta)), eta_max)
            p_nonpow = n_nonpow * LANDAUER_J_PER_BIT_300K / eta
    return pd.DataFrame({
        "year": years,
        "bitops_per_s": n_nonpow + base.pow_bitops,
        "nonpow_landauer_efficiency": eta,
        "power_w": p_nonpow + base.pow_power_w,
    })


def crossing_year(df: pd.DataFrame, threshold_w: float, growth: float = 0.0) -> float:
    target = threshold_w * (1.0 + growth) ** (df["year"].to_numpy() - BASE_YEAR)
    hit = np.nonzero(df["power_w"].to_numpy() >= target)[0]
    return float(df["year"].iloc[hit[0]]) if len(hit) else float("nan")


def eta_year(df: pd.DataFrame, level: float) -> float:
    hit = np.nonzero(df["nonpow_landauer_efficiency"].to_numpy() >= level * (1 - 1e-12))[0]
    return float(df["year"].iloc[hit[0]]) if len(hit) else float("nan")


def _crossings(df: pd.DataFrame) -> dict[str, float]:
    out = {name: crossing_year(df, w) for name, w in THRESHOLDS.items()}
    out["global_primary_energy_growing_1p5pct"] = crossing_year(
        df, CURRENT_GLOBAL_PRIMARY_ENERGY_W, GLOBAL_PRIMARY_ENERGY_GROWTH
    )
    return out


def build_scenarios(base: Baseline, trends: dict[str, Trend]) -> list[dict[str, object]]:
    scenarios: list[dict[str, object]] = []
    for tr in trends.values():
        for eta_max in ETA_CEILINGS:
            df = path(base, tr.g_bitops, tr.g_eta, eta_max)
            scenarios.append({
                "family": "irreversible", "trend_window": tr.window, "g_bitops": tr.g_bitops,
                "g_eta": tr.g_eta, "g_power_before_ceiling": tr.g_power, "eta_max": eta_max,
                "year_eta_reaches_ceiling": eta_year(df, eta_max), "df": df,
            })
        df = path(base, tr.g_bitops, tr.g_eta, None, g_power=tr.g_power)
        scenarios.append({
            "family": "power_trend_requires_reversible", "trend_window": tr.window, "g_bitops": tr.g_bitops,
            "g_eta": tr.g_eta, "g_power_before_ceiling": tr.g_power, "eta_max": float("inf"),
            "year_eta_reaches_ceiling": eta_year(df, 1.0), "df": df,
        })
    modern = trends["modern_2000_2026"]
    for g in DEMAND_SENSITIVITY:
        for eta_max in ETA_CEILINGS:
            df = path(base, g, modern.g_eta, eta_max)
            scenarios.append({
                "family": "demand_sensitivity", "trend_window": "modern_eta_trend", "g_bitops": g,
                "g_eta": modern.g_eta, "g_power_before_ceiling": (1 + g) / (1 + modern.g_eta) - 1,
                "eta_max": eta_max, "year_eta_reaches_ceiling": eta_year(df, eta_max), "df": df,
            })
    for s in scenarios:
        s.update(_crossings(s["df"]))  # type: ignore[arg-type]
    return scenarios


def _label(s: dict[str, object]) -> str:
    if s["family"] == "power_trend_requires_reversible":
        return f"power trend +{100*float(s['g_power_before_ceiling']):.0f}%/yr (needs reversible)"
    return f"irreversible, eta_max={float(s['eta_max']):g}"


THRESHOLD_LABELS = {
    "current_global_primary_energy": "global primary energy (2025)",
    "waste_heat_1pct_absorbed_solar": "1% of absorbed sunlight",
    "earth_intercepted_solar_power": "Earth-intercepted sunlight",
    "solar_luminosity": "solar luminosity",
}


def make_figures(hist: pd.DataFrame, scenarios: list[dict[str, object]], out_figures: Path) -> None:
    out_figures.mkdir(parents=True, exist_ok=True)
    head = [s for s in scenarios if s["trend_window"] == HEADLINE_WINDOW]
    specs = (
        ("power_w", "Wall power for artificial computation (W)", "future_power_projection", (1945, 2200),
         "p50_associated_power_including_pow_w"),
        ("nonpow_landauer_efficiency", "Non-PoW wall Landauer efficiency", "future_eta_projection", (1945, 2150),
         "p50_wall_landauer_efficiency_excluding_pow"),
        ("bitops_per_s", "Functional bit operations per second", "future_bitops_projection", (1945, 2150),
         "p50_bitops_including_pow"),
    )
    for key, ylabel, stem, xlim, hist_col in specs:
        fig, ax = plt.subplots(figsize=(10.5, 6.2))
        h = hist[hist["year"] >= 1945]
        ax.plot(h["year"], h[hist_col], "ko-", markersize=3.5, linewidth=1.4, label="historical model (p50)")
        for s in head:
            df = s["df"]
            sub = df[df["year"] <= xlim[1]]
            ax.plot(sub["year"], sub[key], linewidth=2.0,
                    linestyle="--" if s["family"].startswith("power") else "-", label=_label(s))
        if key == "power_w":
            for name, w in THRESHOLDS.items():
                ax.axhline(w, color="0.35", linewidth=0.9, linestyle=":")
                ax.text(xlim[0] + 3, w * 1.5, THRESHOLD_LABELS[name], fontsize=8, color="0.25")
            ax.set_ylim(1e6, 1e28)
        if key == "nonpow_landauer_efficiency":
            ax.axhline(1.0, color="0.35", linewidth=0.9, linestyle=":")
            ax.text(xlim[0] + 3, 1.6, "Landauer limit (irreversible)", fontsize=8, color="0.25")
            ax.set_ylim(1e-21, 1e6)
        ax.set_yscale("log")
        ax.set_xlim(*xlim)
        ax.set_xlabel("Year")
        ax.set_ylabel(ylabel)
        ax.set_title("Trends holding: fitted 1945-2026 non-PoW trends extrapolated", fontsize=11)
        ax.grid(True, which="major", linewidth=0.45, alpha=0.35)
        ax.legend(fontsize=8, loc="lower right" if key != "nonpow_landauer_efficiency" else "upper left")
        fig.tight_layout()
        fig.savefig(out_figures / f"{stem}.png", dpi=220)
        plt.close(fig)

    fig, ax = plt.subplots(figsize=(10.5, 6.2))
    sens = [s for s in scenarios if s["family"] == "demand_sensitivity" and s["eta_max"] == HEADLINE_ETA_MAX]
    for s in sens:
        sub = s["df"][s["df"]["year"] <= 2300]
        ax.plot(sub["year"], sub["power_w"], linewidth=2.0, label=f"bitops demand +{100*float(s['g_bitops']):.0f}%/yr")
    for name, w in THRESHOLDS.items():
        ax.axhline(w, color="0.35", linewidth=0.9, linestyle=":")
        ax.text(2029, w * 1.5, THRESHOLD_LABELS[name], fontsize=8, color="0.25")
    ax.set_yscale("log")
    ax.set_ylim(1e9, 1e28)
    ax.set_xlim(2026, 2300)
    ax.set_xlabel("Year")
    ax.set_ylabel("Wall power for artificial computation (W)")
    ax.set_title(f"Slower-demand sensitivity (irreversible, eta_max = {HEADLINE_ETA_MAX:g})", fontsize=11)
    ax.grid(True, which="major", linewidth=0.45, alpha=0.35)
    ax.legend(fontsize=8, loc="lower right")
    fig.tight_layout()
    fig.savefig(out_figures / "constant_growth_sensitivity.png", dpi=220)
    fig.savefig(out_figures / "constant_growth_sensitivity.svg")
    plt.close(fig)


def _fmt_year(y: float) -> str:
    return "never (<2700)" if math.isnan(y) else f"{int(y)}"


def run(out_data: Path, out_figures: Path) -> list[dict[str, object]]:
    hist = load_history(out_data)
    base = baseline_from_history(hist)
    trends = fit_trends(hist)
    scenarios = build_scenarios(base, trends)

    cross_cols = list(THRESHOLDS) + ["global_primary_energy_growing_1p5pct"]
    meta_cols = ["family", "trend_window", "g_bitops", "g_eta", "g_power_before_ceiling", "eta_max",
                 "year_eta_reaches_ceiling"]
    with (out_data / "earth_artificial_bitops_future_threshold_crossings.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=meta_cols + cross_cols)
        writer.writeheader()
        for s in scenarios:
            writer.writerow({k: s[k] for k in meta_cols + cross_cols})

    with (out_data / "earth_artificial_bitops_future_trend_fits.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["trend_window", "g_bitops_per_yr", "g_power_per_yr", "g_eta_per_yr"])
        for tr in trends.values():
            writer.writerow([tr.window, tr.g_bitops, tr.g_power, tr.g_eta])

    frames = []
    for s in scenarios:
        if s["trend_window"] != HEADLINE_WINDOW:
            continue
        df = s["df"][s["df"]["year"] <= 2400].copy()
        df.insert(1, "scenario", _label(s))
        frames.append(df)
    pd.concat(frames).to_csv(out_data / "earth_artificial_bitops_future_timeseries.csv", index=False)

    head = {(_s["family"], _s["eta_max"]): _s for _s in scenarios if _s["trend_window"] == HEADLINE_WINDOW}
    central = head[("irreversible", HEADLINE_ETA_MAX)]
    rev = head[("power_trend_requires_reversible", float("inf"))]
    tr = trends[HEADLINE_WINDOW]
    lines = [
        "# Future projection summary",
        "",
        "Generated by `scripts/run_future.py`.  No crossing year is an input; all follow from fitted",
        "non-PoW trends, the 2026 baseline, and an explicit efficiency ceiling.",
        "",
        "## Fitted non-PoW trends",
        "",
        "| Window | Bitops growth | Power growth | eta_L growth |",
        "| --- | ---: | ---: | ---: |",
    ]
    for t in trends.values():
        lines.append(f"| {t.window} | {100*t.g_bitops:.1f}%/yr | {100*t.g_power:.1f}%/yr | {100*t.g_eta:.1f}%/yr |")
    lines += [
        "",
        f"## Crossing years ({HEADLINE_WINDOW} trends)",
        "",
        "| Scenario | eta ceiling reached | Global primary energy | ...growing 1.5%/yr | 1% absorbed sunlight | Earth-intercepted sunlight | Solar luminosity |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for s in scenarios:
        if s["trend_window"] != HEADLINE_WINDOW:
            continue
        lines.append(
            f"| {_label(s)} | {_fmt_year(float(s['year_eta_reaches_ceiling']))} | "
            f"{_fmt_year(float(s['current_global_primary_energy']))} | "
            f"{_fmt_year(float(s['global_primary_energy_growing_1p5pct']))} | "
            f"{_fmt_year(float(s['waste_heat_1pct_absorbed_solar']))} | "
            f"{_fmt_year(float(s['earth_intercepted_solar_power']))} | {_fmt_year(float(s['solar_luminosity']))} |"
        )
    lines += ["", "## Crossing years (modern_2000_2026 trends)", "",
              "| Scenario | eta ceiling reached | Global primary energy | ...growing 1.5%/yr | 1% absorbed sunlight | Earth-intercepted sunlight | Solar luminosity |",
              "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for s in scenarios:
        if s["trend_window"] != "modern_2000_2026":
            continue
        lines.append(
            f"| {_label(s)} | {_fmt_year(float(s['year_eta_reaches_ceiling']))} | "
            f"{_fmt_year(float(s['current_global_primary_energy']))} | "
            f"{_fmt_year(float(s['global_primary_energy_growing_1p5pct']))} | "
            f"{_fmt_year(float(s['waste_heat_1pct_absorbed_solar']))} | "
            f"{_fmt_year(float(s['earth_intercepted_solar_power']))} | {_fmt_year(float(s['solar_luminosity']))} |"
        )
    lines += ["", "## Slower-demand sensitivity (eta improves at the modern trend, then stops at the ceiling)", "",
              "| Bitops demand | eta_max | Global primary energy | 1% absorbed sunlight | Earth-intercepted sunlight | Solar luminosity |",
              "| ---: | ---: | ---: | ---: | ---: | ---: |"]
    for s in scenarios:
        if s["family"] != "demand_sensitivity":
            continue
        lines.append(
            f"| +{100*float(s['g_bitops']):.0f}%/yr | {float(s['eta_max']):g} | "
            f"{_fmt_year(float(s['current_global_primary_energy']))} | {_fmt_year(float(s['waste_heat_1pct_absorbed_solar']))} | "
            f"{_fmt_year(float(s['earth_intercepted_solar_power']))} | {_fmt_year(float(s['solar_luminosity']))} |"
        )
    lines += [
        "",
        f"## Forward table ({HEADLINE_WINDOW} trends: bitops +{100*tr.g_bitops:.0f}%/yr)",
        "",
        f"Irreversible column uses eta_max = {HEADLINE_ETA_MAX:g}.  The power-trend column needs eta_L above the",
        "irreversible ceiling (and above 1 later), i.e. reversible computing.",
        "",
        "| Year | Bitops/s | Irreversible: eta_L | Irreversible: power (W) | x global primary | Power-trend: power (W) | Power-trend: required eta_L |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    c_df, r_df = central["df"].set_index("year"), rev["df"].set_index("year")
    for y in TABLE_YEARS:
        c, r = c_df.loc[y], r_df.loc[y]
        lines.append(
            f"| {y} | {c['bitops_per_s']:.2e} | {c['nonpow_landauer_efficiency']:.1e} | {c['power_w']:.2e} | "
            f"{c['power_w']/CURRENT_GLOBAL_PRIMARY_ENERGY_W:.2g} | {r['power_w']:.2e} | {r['nonpow_landauer_efficiency']:.1e} |"
        )
    (out_data / "earth_artificial_bitops_future_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    make_figures(hist, scenarios, out_figures)
    return scenarios
