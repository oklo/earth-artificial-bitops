"""Generate the talk-facing population/time table."""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt

from earth_bitops.formatting import sci_tex, source_label


ROWS = [
    (1940, 3.9e6, "relay/electromechanical and special-purpose machines"),
    (1950, 3.0e8, "early stored-program electronic computers"),
    (1960, 3.0e10, "mainframes and military/scientific systems"),
    (1970, 3.0e12, "mainframes, minicomputers, early embedded control"),
    (1980, 3.0e14, "microprocessors, minicomputers, early PCs"),
    (1990, 3.0e16, "PCs, workstations, mainframes, embedded systems"),
    (1995, 5.0e17, "internet-era PCs and servers"),
    (2000, 1.1e19, "PC/web era plus data centres"),
    (2005, 3.0e20, "cloud, GPUs, mobile ramp"),
    (2010, 2.5e21, "smartphones, cloud, early PoW"),
    (2015, 7.3e22, "cloud plus SHA-256 PoW"),
    (2020, 1.3e25, "SHA-256 PoW with cloud/accelerator growth"),
    (2025, 7.9e25, "estimated current/reconstructed row; SHA-256 PoW plus accelerator-scale compute"),
    (2030, 1.9e27, "qualitative: likely SHA-256 PoW plus AI/accelerator-scale compute"),
    (2035, 4.5e28, "qualitative forward extrapolation of aggregate bitops"),
]


def write_table(data_dir: Path, figures_dir: Path) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)
    rows = [
        {
            "year": year,
            "inclusive_bitops_per_s": bitops,
            "display_bitops_per_s": sci_tex(bitops, digits=2),
            "status": source_label(year),
            "interpretation": interpretation,
        }
        for year, bitops, interpretation in ROWS
    ]
    with (data_dir / "earth_artificial_bitops_population_table.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    md_lines = ["# Talk table: artificial computation on Earth", "", "| Year | Bitops/s | Status | Interpretation |", "| ---: | ---: | --- | --- |"]
    for row in rows:
        md_lines.append(
            f"| {row['year']} | {row['display_bitops_per_s']} | {row['status']} | {row['interpretation']} |"
        )
    (data_dir / "earth_artificial_bitops_population_table.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    fig, ax = plt.subplots(figsize=(13.5, 7.6))
    ax.axis("off")
    table_rows = [
        [str(row["year"]), row["display_bitops_per_s"].replace(" x ", "\nx "), row["status"], row["interpretation"]]
        for row in rows
    ]
    table = ax.table(
        cellText=table_rows,
        colLabels=["Year", "Functional bitops/s", "Status", "Qualitative contributor note"],
        loc="center",
        cellLoc="left",
        colLoc="left",
        colWidths=[0.08, 0.18, 0.20, 0.54],
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
