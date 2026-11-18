"""Generate the talk-facing bitops and energy tables (1945 onward).

Every number is derived from generated model outputs:
  * 1945-2025 rows: Monte Carlo historical model (p50).
  * 2030 and 2035 rows: component projection (p50).
No row is hand-entered.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from earth_bitops.constants import (
    CURRENT_GLOBAL_PRIMARY_ENERGY_W,
    LANDAUER_J_PER_BIT_300K,
    SECONDS_PER_JULIAN_YEAR,
    WORLD_POPULATION,
)
from earth_bitops.formatting import sci_tex
from earth_bitops.plotting import GROUP_ORDER

TABLE_YEARS = (1945, 1950, 1960, 1970, 1980, 1990, 1995, 2000, 2005, 2010, 2015, 2020, 2025, 2030, 2035)
ERG_PER_JOULE = 1e7
CONTRIBUTOR_MIN_SHARE = 0.10


def _contributors(plot_row: pd.Series) -> str:
    total = float(plot_row["total_bitops_including_pow"])
    shares = {g: float(plot_row[f"bitops_{g}"]) / total for g in GROUP_ORDER}
    top = sorted(shares.items(), key=lambda kv: -kv[1])
    kept = [f"{g} ({100*s:.0f}%)" for g, s in top if s >= CONTRIBUTOR_MIN_SHARE]
    if len(kept) < 2 and len(top) > 1 and top[1][1] >= 0.005:
        kept.append(f"{top[1][0]} ({100*top[1][1]:.1f}%)")
    return "; ".join(kept)


def build_rows(data_dir: Path) -> pd.DataFrame:
    plot = pd.read_csv(data_dir / "earth_artificial_bitops_diagram_plot_data.csv").set_index("year")
    rows = []
    for year in TABLE_YEARS:
        r = plot.loc[year]
        n_incl, n_excl = float(r["total_bitops_including_pow"]), float(r["total_bitops_excluding_pow"])
        p_incl, p_excl = float(r["power_including_pow_w"]), float(r["power_excluding_pow_w"])
        pop = WORLD_POPULATION[year]
        energy_j = p_incl * SECONDS_PER_JULIAN_YEAR
        rows.append({
            "year": year,
            "basis": "projection (p50)" if bool(r["projected"]) else "historical model (p50)",
            "bitops_per_s_including_pow": n_incl,
            "bitops_per_s_excluding_pow": n_excl,
            "bitops_per_year_including_pow": n_incl * SECONDS_PER_JULIAN_YEAR,
            "power_w_including_pow": p_incl,
            "power_w_excluding_pow": p_excl,
            "energy_twh_per_year": energy_j / 3.6e15,
            "energy_erg_per_year": energy_j * ERG_PER_JOULE,
            "fraction_of_2025_global_primary_energy": p_incl / CURRENT_GLOBAL_PRIMARY_ENERGY_W,
            "bitops_per_erg_including_pow": n_incl / (p_incl * ERG_PER_JOULE),
            "bitops_per_erg_excluding_pow": n_excl / (p_excl * ERG_PER_JOULE),
            "landauer_efficiency_including_pow": n_incl * LANDAUER_J_PER_BIT_300K / p_incl,
            "landauer_efficiency_excluding_pow": n_excl * LANDAUER_J_PER_BIT_300K / p_excl,
            "world_population": pop,
            "bitops_per_person_per_year": n_incl * SECONDS_PER_JULIAN_YEAR / pop,
            "energy_kwh_per_person_per_year": energy_j / 3.6e6 / pop,
            "primary_contributors": _contributors(r),
        })
    return pd.DataFrame(rows)


def _kwh(x: float) -> str:
    return f"{x:.3f} kWh" if x < 1 else (f"{x:.2f} kWh" if x < 10 else (f"{x:.1f} kWh" if x < 100 else f"{x:.0f} kWh"))


def _twh(x: float) -> str:
    return f"{x:,.0f}" if x >= 100 else f"{x:.3g}"


def _pct(x: float) -> str:
    return f"{x:.2g}%" if x >= 0.01 else f"{float(f'{x:.1g}'):.5f}".rstrip("0") + "%"


def _power(w: float) -> str:
    return f"{w/1e6:.0f} MW" if w < 9.995e8 else f"{w/1e9:.1f} GW" if w < 1e11 else f"{w/1e9:.0f} GW"


def markdown_tables(df: pd.DataFrame) -> tuple[str, str]:
    t1 = [
        "| Year | Bitops/s (all) | Bitops/s (non-PoW) | eta_L (all) | eta_L (non-PoW) | Bitops/person/yr | Energy/person/yr | Primary contributors (share of all bitops) |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    t2 = [
        "| Year | Wall power | Energy/yr (TWh) | Energy/yr (erg) | Bitops/yr | Bitops/erg (all) | Bitops/erg (non-PoW) | Share of 2025 world primary energy |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for _, r in df.iterrows():
        mark = "*" if r["basis"].startswith("projection") else ""
        t1.append(
            f"| {r['year']}{mark} | `{sci_tex(r['bitops_per_s_including_pow'])}` | `{sci_tex(r['bitops_per_s_excluding_pow'])}` | "
            f"`{sci_tex(r['landauer_efficiency_including_pow'])}` | `{sci_tex(r['landauer_efficiency_excluding_pow'])}` | "
            f"`{sci_tex(r['bitops_per_person_per_year'])}` | {_kwh(r['energy_kwh_per_person_per_year'])} | {r['primary_contributors']} |"
        )
        twh = r["energy_twh_per_year"]
        t2.append(
            f"| {r['year']}{mark} | {_power(r['power_w_including_pow'])} | {_twh(twh)} | `{sci_tex(r['energy_erg_per_year'])}` | "
            f"`{sci_tex(r['bitops_per_year_including_pow'])}` | `{sci_tex(r['bitops_per_erg_including_pow'])}` | "
            f"`{sci_tex(r['bitops_per_erg_excluding_pow'])}` | {_pct(100*r['fraction_of_2025_global_primary_energy'])} |"
        )
    return "\n".join(t1), "\n".join(t2)


def write_table(data_dir: Path, figures_dir: Path) -> None:
    figures_dir.mkdir(parents=True, exist_ok=True)
    df = build_rows(data_dir)
    df.to_csv(data_dir / "earth_artificial_bitops_population_table.csv", index=False)
    t1, t2 = markdown_tables(df)
    note = "\n\n`*` = projection (component model, p50).  All other rows are historical-model p50 values.\n"
    (data_dir / "earth_artificial_bitops_population_table.md").write_text(
        "# Talk table: artificial computation on Earth, 1945 onward\n\n## Bitops\n\n" + t1
        + "\n\n## Energy\n\n" + t2 + note, encoding="utf-8")

    fig, ax = plt.subplots(figsize=(15.5, 7.8))
    ax.axis("off")
    cells = [[
        f"{r['year']}{'*' if r['basis'].startswith('projection') else ''}",
        sci_tex(r["bitops_per_s_including_pow"]), sci_tex(r["bitops_per_s_excluding_pow"]),
        _power(r["power_w_including_pow"]),
        sci_tex(r["landauer_efficiency_including_pow"]), sci_tex(r["landauer_efficiency_excluding_pow"]),
        sci_tex(r["bitops_per_person_per_year"]), _kwh(r["energy_kwh_per_person_per_year"]),
        r["primary_contributors"],
    ] for _, r in df.iterrows()]
    table = ax.table(
        cellText=cells,
        colLabels=["Year", "Bitops/s\n(all)", "Bitops/s\n(non-PoW)", "Wall\npower", "eta_L\n(all)", "eta_L\n(non-PoW)",
                   "Bitops /\nperson / yr", "Energy /\nperson / yr", "Primary contributors (share of all bitops)"],
        loc="center", cellLoc="left", colLoc="left",
        colWidths=[0.045, 0.085, 0.085, 0.06, 0.085, 0.085, 0.085, 0.075, 0.395],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9.5)
    table.scale(1.0, 1.7)
    for (r, _c), cell in table.get_celld().items():
        cell.set_edgecolor("#dddddd")
        if r == 0:
            cell.set_text_props(weight="bold")
            cell.set_facecolor("#f2f2f2")
            cell.set_height(cell.get_height() * 1.5)
    ax.text(0.0, 0.01, "* projection (component model, p50)", transform=ax.transAxes, fontsize=9, color="0.3")
    fig.tight_layout()
    fig.savefig(figures_dir / "population_table_zoom_readable.png", dpi=220)
    fig.savefig(figures_dir / "population_table_zoom_readable.svg")
    plt.close(fig)
