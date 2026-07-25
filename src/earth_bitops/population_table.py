"""Generate the talk-facing population/time table."""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt

from earth_bitops.formatting import sci_tex


ROWS = [
    (1940, 3.98e6, 1.14e-21, 5.46e4, "0.038 kWh", "Punched-card, relay, electromechanical, analog"),
    (1950, 3.01e8, 4.35e-20, 3.81e6, "0.070 kWh", "Early electronic + electromechanical business machines"),
    (1960, 3.02e10, 4.32e-19, 3.16e8, "0.582 kWh", "Commercial/scientific computers"),
    (1970, 2.98e12, 8.61e-18, 2.55e10, "2.36 kWh", "Mainframes, minis, early IC systems"),
    (1980, 2.99e14, 2.87e-16, 2.12e12, "5.91 kWh", "Embedded / app-specific logic; mainframes/minis; PCs/consoles"),
    (1990, 2.98e16, 8.57e-15, 1.76e14, "16.4 kWh", "Embedded / app-specific logic; PCs/workstations; servers/mainframes"),
    (1995, 4.96e17, 9.52e-14, 2.72e15, "22.7 kWh", "Embedded / app-specific logic; PCs/consoles; servers/data centres"),
    (2000, 1.15e19, 1.37e-12, 5.87e16, "34.1 kWh", "Embedded logic; PCs/consoles; servers/data centres; telecom/mobile"),
    (2005, 3.00e20, 1.96e-11, 1.44e18, "58.6 kWh", "Embedded logic; PCs/consoles; telecom; servers/data centres; mobile"),
    (2010, 2.50e21, 1.20e-10, 1.12e19, "74.8 kWh", "Embedded logic; PCs/consoles; phones/tablets; telecom/consumer media"),
    (2015, 7.25e22, 2.96e-9, 3.06e20, "82.5 kWh", "SHA-256 PoW; embedded logic; AI/deep-learning GPUs"),
    (2020, 1.29e25, 3.88e-7, 5.15e22, "106 kWh", "SHA-256 PoW dominates; AI accelerators; embedded logic"),
    (2025, 7.90e25, 1.40e-6, 3.03e23, "173 kWh", "2025 estimate; SHA-256 PoW still dominant; AI accelerators rising"),
    (2030, 1.89e27, 2.29e-5, 6.95e24, "242 kWh", "Extrapolated; likely SHA-256 PoW + AI/accelerator-scale compute"),
    (2035, 4.51e28, 3.76e-4, 1.60e26, "340 kWh", "Extrapolated; high-throughput ASIC/accelerator compute likely dominant"),
]


def write_table(data_dir: Path, figures_dir: Path) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)
    rows = [
        {
            "year": year,
            "inclusive_bitops_per_s": bitops,
            "display_bitops_per_s": sci_tex(bitops, digits=2),
            "average_landauer_efficiency": eta,
            "display_average_landauer_efficiency": sci_tex(eta, digits=2),
            "bitops_per_person_per_year": per_capita_bitops,
            "display_bitops_per_person_per_year": sci_tex(per_capita_bitops, digits=2),
            "energy_per_person_per_year": energy_per_person,
            "primary_contributors": contributors,
        }
        for year, bitops, eta, per_capita_bitops, energy_per_person, contributors in ROWS
    ]
    with (data_dir / "earth_artificial_bitops_population_table.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    md_lines = [
        "# Talk table: artificial computation on Earth",
        "",
        "| Year | Bitops/sec | Avg. Landauer eta_L | Bitops/person/year | Energy/person/year | Primary contributor/year |",
        "| ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        md_lines.append(
            f"| {row['year']} | {row['display_bitops_per_s']} | "
            f"{row['display_average_landauer_efficiency']} | "
            f"{row['display_bitops_per_person_per_year']} | "
            f"{row['energy_per_person_per_year']} | {row['primary_contributors']} |"
        )
    (data_dir / "earth_artificial_bitops_population_table.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    fig, ax = plt.subplots(figsize=(13.5, 7.6))
    ax.axis("off")
    table_rows = [
        [
            str(row["year"]),
            row["display_bitops_per_s"].replace(" x ", "\nx "),
            row["display_average_landauer_efficiency"].replace(" x ", "\nx "),
            row["display_bitops_per_person_per_year"].replace(" x ", "\nx "),
            row["energy_per_person_per_year"],
            row["primary_contributors"],
        ]
        for row in rows
    ]
    table = ax.table(
        cellText=table_rows,
        colLabels=[
            "Year",
            "Bitops/sec",
            "Avg. Landauer\neta_L",
            "Bitops /\nperson / year",
            "Energy /\nperson / year",
            "Primary contributors to bitops count",
        ],
        loc="center",
        cellLoc="left",
        colLoc="left",
        colWidths=[0.07, 0.14, 0.14, 0.16, 0.13, 0.36],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(12)
    table.scale(1.0, 1.75)
    for (r, _c), cell in table.get_celld().items():
        cell.set_edgecolor("#dddddd")
        if r == 0:
            cell.set_text_props(weight="bold")
            cell.set_facecolor("#f2f2f2")
    fig.tight_layout()
    fig.savefig(figures_dir / "population_table_zoom_readable.png", dpi=220)
    fig.savefig(figures_dir / "population_table_zoom_readable.svg")
    plt.close(fig)
