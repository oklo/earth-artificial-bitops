#!/usr/bin/env python3
"""
earth_artificial_bitops_historical_model.py

Historical extension of the Earth artificial computation model.

Metric
------
The numerator is the same as the current-day model:

    functional one-bit primitive operations per second

meaning one-bit Boolean operations, one-bit adder-slice operations, and
multiply partial-products implied by actual digital workloads.  This is not a
transistor-switching count, an instruction count, a FLOP count, or a bit-motion
count.

Landauer efficiency is reported as:

    eta_L = bitops_per_second * k_B * T * ln(2) / associated_power_watts

where associated_power_watts is a system/wall denominator unless otherwise
stated.  A narrower logic-only denominator is also reported.

Historical strategy
-------------------
This file uses a deliberately transparent two-layer model:

1. non-PoW artificial computation, represented as actual realized bitops/s and
   associated wall power.  For 1986-2007 it is anchored by Hilbert & Lopez-style
   installed instruction-per-second estimates, converted to realized functional
   bitops using broad factors.  For 2000+ the power denominator is anchored by
   published data-centre and network electricity estimates.  For pre-1980 the
   anchors are broad order-of-magnitude extrapolations constrained by early
   computer counts, machine performance, and Koomey-law energy-efficiency trends.

2. SHA-256 proof-of-work, represented as network hash rate * bitops/hash.  The
   power denominator uses historical fleet efficiency in J/TH plus overhead.
   Bitcoin is zero before 2009 and negligible in this model before 2010.

The aim is not false precision.  The p10/p50/p90 intervals are intentionally
wide, especially before 1980 and around the utilization conversion from
installed capacity to actual realized operations.

Run:
    python earth_artificial_bitops_historical_model.py --samples 300000 --seed 20260603 --out-dir data/processed
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

try:
    import matplotlib.pyplot as plt
except Exception:  # pragma: no cover - plot is optional
    plt = None

Z10 = 1.2815515655446004
BOLTZMANN_J_PER_K = 1.380_649e-23
LN2 = math.log(2.0)
# New years are appended so the random stream for the original years is unchanged.
TARGET_YEARS = [2026, 2020, 2015, 2010, 2005, 2000, 1995, 1990, 1980, 1970, 1960, 1950, 1940, 1945, 2025]


@dataclass(frozen=True)
class LogQuantile:
    """Positive uncertain scalar represented by p10/p50/p90 quantiles."""

    p10: float
    p50: float
    p90: float

    def sample(self, rng: np.random.Generator, n: int) -> np.ndarray:
        if self.p10 <= 0 or self.p50 <= 0 or self.p90 <= 0:
            raise ValueError(f"quantiles must be positive: {self}")
        if not (self.p10 <= self.p50 <= self.p90):
            raise ValueError(f"require p10 <= p50 <= p90: {self}")
        sigma = (math.log(self.p90) - math.log(self.p10)) / (2.0 * Z10)
        return rng.lognormal(mean=math.log(self.p50), sigma=sigma, size=n)


def q_from_multipliers(p50: float, lower: float, upper: float) -> LogQuantile:
    """Build p10/p50/p90 from multiplicative lower/upper factors around p50."""
    return LogQuantile(p10=p50 * lower, p50=p50, p90=p50 * upper)


@dataclass(frozen=True)
class NonPoWAnchor:
    year: int
    bitops: LogQuantile
    associated_power_w: LogQuantile
    logic_power_fraction: LogQuantile
    source_class: str
    note: str


@dataclass(frozen=True)
class PoWAnchor:
    year: int
    hash_rate_hps: LogQuantile | None
    bitops_per_hash: LogQuantile | None
    other_sha256_multiplier: LogQuantile | None
    fleet_efficiency_j_per_th: LogQuantile | None
    site_overhead_multiplier: LogQuantile | None
    note: str


@dataclass(frozen=True)
class YearSummary:
    year: int
    p10_bitops_including_pow: float
    p50_bitops_including_pow: float
    p90_bitops_including_pow: float
    p10_bitops_excluding_pow: float
    p50_bitops_excluding_pow: float
    p90_bitops_excluding_pow: float
    p10_associated_power_including_pow_w: float
    p50_associated_power_including_pow_w: float
    p90_associated_power_including_pow_w: float
    p10_associated_power_excluding_pow_w: float
    p50_associated_power_excluding_pow_w: float
    p90_associated_power_excluding_pow_w: float
    p10_wall_landauer_efficiency_including_pow: float
    p50_wall_landauer_efficiency_including_pow: float
    p90_wall_landauer_efficiency_including_pow: float
    p10_wall_landauer_efficiency_excluding_pow: float
    p50_wall_landauer_efficiency_excluding_pow: float
    p90_wall_landauer_efficiency_excluding_pow: float
    p10_logic_landauer_efficiency_including_pow: float
    p50_logic_landauer_efficiency_including_pow: float
    p90_logic_landauer_efficiency_including_pow: float
    p10_logic_landauer_efficiency_excluding_pow: float
    p50_logic_landauer_efficiency_excluding_pow: float
    p90_logic_landauer_efficiency_excluding_pow: float
    p50_logic_power_including_pow_w: float
    p50_logic_power_excluding_pow_w: float
    p50_wall_factor_above_landauer_including_pow: float
    p50_wall_factor_above_landauer_excluding_pow: float
    p50_logic_factor_above_landauer_including_pow: float
    p50_logic_factor_above_landauer_excluding_pow: float
    p50_pow_share_of_bitops: float
    p50_pow_share_of_power: float


@dataclass(frozen=True)
class CategorySummary:
    year: int
    category: str
    p10_bitops: float
    p50_bitops: float
    p90_bitops: float
    p10_associated_power_w: float
    p50_associated_power_w: float
    p90_associated_power_w: float
    p50_wall_landauer_efficiency: float
    note: str


# Non-PoW anchors: actual realized functional bitops/s, not installed peak.
# p50 values are smooth, source-constrained order-of-magnitude anchors.  The
# intervals are wide because the conversion from installed capacity and device
# power to actual functional bitops is not directly observed.
NON_POW_ANCHORS: dict[int, NonPoWAnchor] = {
    1940: NonPoWAnchor(
        1940,
        q_from_multipliers(4.0e6, 1e-2, 1e2),
        q_from_multipliers(1.0e7, 0.15, 7.0),
        LogQuantile(0.05, 0.20, 0.60),
        "pre-electronic / electromechanical extrapolation",
        "Late relay/electromechanical tabulation and special-purpose wartime machines; deliberately very broad.",
    ),
    1945: NonPoWAnchor(
        1945,
        q_from_multipliers(3.5e7, 1e-2, 70.0),
        q_from_multipliers(1.4e7, 0.18, 6.0),
        LogQuantile(0.05, 0.20, 0.60),
        "log-interpolated between the 1940 and 1950 anchors",
        "Colossus/ENIAC-era one-off electronic machines on top of relay and punched-card computation; geometric mean of neighbours.",
    ),
    1950: NonPoWAnchor(
        1950,
        q_from_multipliers(3.0e8, 0.02, 50.0),
        q_from_multipliers(2.0e7, 0.20, 5.0),
        LogQuantile(0.05, 0.20, 0.60),
        "early stored-program extrapolation",
        "A handful-to-dozens of large electronic machines plus relay/electromechanical computing.",
    ),
    1960: NonPoWAnchor(
        1960,
        q_from_multipliers(3.0e10, 0.04, 25.0),
        q_from_multipliers(2.0e8, 0.25, 4.0),
        LogQuantile(0.06, 0.22, 0.65),
        "mainframe era extrapolation",
        "Commercial mainframes, SAGE-scale military systems, early transistor machines.",
    ),
    1970: NonPoWAnchor(
        1970,
        q_from_multipliers(3.0e12, 0.06, 17.0),
        q_from_multipliers(1.0e9, 0.30, 3.0),
        LogQuantile(0.07, 0.24, 0.70),
        "mainframe/minicomputer extrapolation",
        "Mainframes plus rapidly expanding minicomputers and embedded control.",
    ),
    1980: NonPoWAnchor(
        1980,
        q_from_multipliers(3.0e14, 0.08, 12.0),
        q_from_multipliers(3.0e9, 0.35, 2.6),
        LogQuantile(0.08, 0.26, 0.72),
        "microprocessor transition extrapolation",
        "Mainframes/minicomputers plus early personal computers, consoles, calculators, and embedded microprocessors.",
    ),
    1990: NonPoWAnchor(
        1990,
        q_from_multipliers(3.0e16, 0.12, 8.0),
        q_from_multipliers(1.0e10, 0.45, 2.3),
        LogQuantile(0.09, 0.28, 0.75),
        "Hilbert/Lopez-interpolated capacity converted to actual bitops",
        "Interpolated between 1986 and 1993 global MIPS capacity anchors, then converted to realized functional bitops.",
    ),
    1995: NonPoWAnchor(
        1995,
        q_from_multipliers(5.0e17, 0.15, 6.5),
        q_from_multipliers(1.5e10, 0.50, 2.0),
        LogQuantile(0.10, 0.30, 0.78),
        "Hilbert/Lopez-interpolated capacity converted to actual bitops",
        "Interpolated between 1993 and 2000 global MIPS capacity anchors; web/PC expansion era.",
    ),
    2000: NonPoWAnchor(
        2000,
        q_from_multipliers(1.15e19, 0.20, 5.0),
        q_from_multipliers(2.4e10, 0.55, 1.8),
        LogQuantile(0.11, 0.32, 0.80),
        "Hilbert/Lopez capacity + Koomey data-centre power anchor",
        "PC peak in general-purpose capacity; data-centre wall power anchored near 70.8 TWh/year plus end-user/embedded/networking.",
    ),
    2005: NonPoWAnchor(
        2005,
        q_from_multipliers(3.0e20, 0.20, 5.0),
        q_from_multipliers(4.4e10, 0.55, 1.8),
        LogQuantile(0.12, 0.33, 0.82),
        "Hilbert/Lopez capacity + Koomey data-centre power anchor",
        "Fast GPU/application-specific growth; data-centre wall power anchored near 152.5 TWh/year plus network/end-user/embedded.",
    ),
    2010: NonPoWAnchor(
        2010,
        q_from_multipliers(2.5e21, 0.22, 4.5),
        q_from_multipliers(6.0e10, 0.60, 1.7),
        LogQuantile(0.12, 0.34, 0.82),
        "post-Hilbert extrapolation + data-centre/network power anchors",
        "Smartphone and cloud era; data centres anchored near 194 TWh/year.",
    ),
    2015: NonPoWAnchor(
        2015,
        q_from_multipliers(1.5e22, 0.20, 5.5),
        q_from_multipliers(7.0e10, 0.62, 1.65),
        LogQuantile(0.13, 0.35, 0.84),
        "IEA data-centre/network power + post-Hilbert extrapolation",
        "Cloud, mobile, consoles, conventional accelerators; data centres and transmission networks roughly 200 and 220 TWh/year respectively.",
    ),
    2020: NonPoWAnchor(
        2020,
        q_from_multipliers(8.0e22, 0.18, 7.0),
        q_from_multipliers(8.5e10, 0.62, 1.75),
        LogQuantile(0.13, 0.36, 0.85),
        "IEA/Masanet-style power + AI-accelerator ramp extrapolation",
        "Pre-generative-AI but GPU/TPU usage is material; data centres near low-200 TWh/year and networks rising.",
    ),
    2025: NonPoWAnchor(
        2025,
        q_from_multipliers(8.5e23, 0.20, 6.0),
        q_from_multipliers(1.39e11, 0.70, 1.60),
        LogQuantile(0.14, 0.38, 0.88),
        "log-interpolated between the 2020 and 2026 anchors",
        "AI-accelerator ramp year; IEA puts data centres at ~485 TWh (AI-focused ~155 TWh) in 2025.",
    ),
    2026: NonPoWAnchor(
        2026,
        q_from_multipliers(1.35e24, 0.20, 6.0),
        q_from_multipliers(1.52e11, 0.70, 1.60),
        LogQuantile(0.14, 0.38, 0.88),
        "current-day anchor from detailed 2026 point estimate",
        "Current non-PoW artificial computation; dominated by AI accelerators, with conventional data centres, networks, PCs, phones and embedded devices as secondary contributors.",
    ),
}

# SHA-256 proof-of-work anchors.  Pre-2010 is zero by construction.
# Hash-rate anchors are p50 order-of-magnitude historical averages for the
# requested year, not exact point observations.
POW_ANCHORS: dict[int, PoWAnchor] = {
    year: PoWAnchor(year, None, None, None, None, None, "No Bitcoin/SHA-256 proof-of-work bucket in this model.")
    for year in [1940, 1945, 1950, 1960, 1970, 1980, 1990, 1995, 2000, 2005]
}
POW_ANCHORS.update(
    {
        2010: PoWAnchor(
            2010,
            q_from_multipliers(1.0e10, 0.10, 10.0),
            LogQuantile(3.0e4, 1.0e5, 2.5e5),
            LogQuantile(1.00, 1.02, 1.15),
            LogQuantile(5.0e6, 3.0e7, 2.0e8),
            LogQuantile(1.02, 1.10, 1.30),
            "Early CPU/GPU Bitcoin mining; CBECI treats pre-July-2010 electricity as negligible in cumulative terms.",
        ),
        2015: PoWAnchor(
            2015,
            q_from_multipliers(4.0e17, 0.45, 2.2),
            LogQuantile(3.0e4, 1.0e5, 2.5e5),
            LogQuantile(1.00, 1.08, 1.35),
            LogQuantile(250.0, 600.0, 1500.0),
            LogQuantile(1.02, 1.08, 1.25),
            "ASIC-era Bitcoin mining; other SHA-256 PoW is small but not forced to zero.",
        ),
        2010 + 10: PoWAnchor(
            2020,
            q_from_multipliers(1.2e20, 0.55, 1.7),
            LogQuantile(3.0e4, 1.0e5, 2.5e5),
            LogQuantile(1.00, 1.05, 1.25),
            LogQuantile(40.0, 65.0, 110.0),
            LogQuantile(1.02, 1.08, 1.22),
            "Large-scale ASIC mining; hash-rate and fleet efficiency dominate the inclusive estimate.",
        ),
        2026: PoWAnchor(
            2026,
            q_from_multipliers(9.8e20, 0.80, 1.25),
            LogQuantile(3.0e4, 1.0e5, 2.5e5),
            LogQuantile(1.00, 1.03, 1.12),
            LogQuantile(14.0, 21.0, 34.0),
            LogQuantile(1.02, 1.08, 1.20),
            "Near-zettahash/s SHA-256 PoW (about 1.0 ZH/s 7-day average, Oct 2026); fleet efficiency ~20-21.5 J/TH (J.P. Morgan).",
        ),
        2025: PoWAnchor(
            2025,
            q_from_multipliers(9.3e20, 0.85, 1.15),
            LogQuantile(3.0e4, 1.0e5, 2.5e5),
            LogQuantile(1.00, 1.03, 1.12),
            LogQuantile(15.0, 22.0, 36.0),
            LogQuantile(1.02, 1.08, 1.20),
            "2025 average hashrate ~0.8-1.09 ZH/s; fleet efficiency ~21.5-22 J/TH (J.P. Morgan Q2-Q3 2025).",
        ),
    }
)


def quantiles(x: np.ndarray) -> tuple[float, float, float]:
    p10, p50, p90 = np.quantile(x, [0.10, 0.50, 0.90])
    return float(p10), float(p50), float(p90)


def sample_year(year: int, rng: np.random.Generator, n: int) -> tuple[YearSummary, list[CategorySummary]]:
    if year not in NON_POW_ANCHORS:
        raise KeyError(year)
    nonpow = NON_POW_ANCHORS[year]
    pow_anchor = POW_ANCHORS[year]

    temp_k = LogQuantile(285.0, 300.0, 315.0).sample(rng, n)
    e_landauer = BOLTZMANN_J_PER_K * temp_k * LN2

    nonpow_bitops = nonpow.bitops.sample(rng, n)
    nonpow_power = nonpow.associated_power_w.sample(rng, n)
    nonpow_logic_fraction = np.minimum(nonpow.logic_power_fraction.sample(rng, n), 0.98)
    nonpow_logic_power = nonpow_power * nonpow_logic_fraction

    category_rows: list[CategorySummary] = []
    nb10, nb50, nb90 = quantiles(nonpow_bitops)
    np10, np50, np90 = quantiles(nonpow_power)
    category_rows.append(
        CategorySummary(
            year=year,
            category="Non-PoW artificial computation",
            p10_bitops=nb10,
            p50_bitops=nb50,
            p90_bitops=nb90,
            p10_associated_power_w=np10,
            p50_associated_power_w=np50,
            p90_associated_power_w=np90,
            p50_wall_landauer_efficiency=float(np.median(nonpow_bitops * e_landauer / nonpow_power)),
            note=f"{nonpow.source_class}: {nonpow.note}",
        )
    )

    if pow_anchor.hash_rate_hps is None:
        pow_bitops = np.zeros(n)
        pow_power = np.zeros(n)
        pow_logic_power = np.zeros(n)
        category_rows.append(
            CategorySummary(
                year=year,
                category="SHA-256 proof-of-work",
                p10_bitops=0.0,
                p50_bitops=0.0,
                p90_bitops=0.0,
                p10_associated_power_w=0.0,
                p50_associated_power_w=0.0,
                p90_associated_power_w=0.0,
                p50_wall_landauer_efficiency=0.0,
                note=pow_anchor.note,
            )
        )
    else:
        h = pow_anchor.hash_rate_hps.sample(rng, n)
        bitops_per_hash = pow_anchor.bitops_per_hash.sample(rng, n)  # type: ignore[union-attr]
        other = pow_anchor.other_sha256_multiplier.sample(rng, n)  # type: ignore[union-attr]
        j_per_th = pow_anchor.fleet_efficiency_j_per_th.sample(rng, n)  # type: ignore[union-attr]
        overhead = pow_anchor.site_overhead_multiplier.sample(rng, n)  # type: ignore[union-attr]
        pow_bitops = h * bitops_per_hash * other
        pow_power = (h / 1.0e12) * j_per_th * other * overhead
        pow_logic_power = (h / 1.0e12) * j_per_th * other
        pb10, pb50, pb90 = quantiles(pow_bitops)
        pp10, pp50, pp90 = quantiles(pow_power)
        category_rows.append(
            CategorySummary(
                year=year,
                category="SHA-256 proof-of-work",
                p10_bitops=pb10,
                p50_bitops=pb50,
                p90_bitops=pb90,
                p10_associated_power_w=pp10,
                p50_associated_power_w=pp50,
                p90_associated_power_w=pp90,
                p50_wall_landauer_efficiency=float(np.median(pow_bitops * e_landauer / pow_power)),
                note=pow_anchor.note,
            )
        )

    bitops_incl = nonpow_bitops + pow_bitops
    bitops_excl = nonpow_bitops
    power_incl = nonpow_power + pow_power
    power_excl = nonpow_power
    logic_power_incl = nonpow_logic_power + pow_logic_power
    logic_power_excl = nonpow_logic_power

    eta_wall_incl = bitops_incl * e_landauer / power_incl
    eta_wall_excl = bitops_excl * e_landauer / power_excl
    eta_logic_incl = bitops_incl * e_landauer / logic_power_incl
    eta_logic_excl = bitops_excl * e_landauer / logic_power_excl

    li10, li50, li90 = quantiles(eta_logic_incl)
    le10, le50, le90 = quantiles(eta_logic_excl)
    lpi10, lpi50, lpi90 = quantiles(logic_power_incl)
    lpe10, lpe50, lpe90 = quantiles(logic_power_excl)
    _ = (lpi10, lpi90, lpe10, lpe90)

    bi10, bi50, bi90 = quantiles(bitops_incl)
    be10, be50, be90 = quantiles(bitops_excl)
    pi10, pi50, pi90 = quantiles(power_incl)
    pe10, pe50, pe90 = quantiles(power_excl)
    ei10, ei50, ei90 = quantiles(eta_wall_incl)
    ee10, ee50, ee90 = quantiles(eta_wall_excl)

    summary = YearSummary(
        year=year,
        p10_bitops_including_pow=bi10,
        p50_bitops_including_pow=bi50,
        p90_bitops_including_pow=bi90,
        p10_bitops_excluding_pow=be10,
        p50_bitops_excluding_pow=be50,
        p90_bitops_excluding_pow=be90,
        p10_associated_power_including_pow_w=pi10,
        p50_associated_power_including_pow_w=pi50,
        p90_associated_power_including_pow_w=pi90,
        p10_associated_power_excluding_pow_w=pe10,
        p50_associated_power_excluding_pow_w=pe50,
        p90_associated_power_excluding_pow_w=pe90,
        p10_wall_landauer_efficiency_including_pow=ei10,
        p50_wall_landauer_efficiency_including_pow=ei50,
        p90_wall_landauer_efficiency_including_pow=ei90,
        p10_wall_landauer_efficiency_excluding_pow=ee10,
        p50_wall_landauer_efficiency_excluding_pow=ee50,
        p90_wall_landauer_efficiency_excluding_pow=ee90,
        p10_logic_landauer_efficiency_including_pow=li10,
        p50_logic_landauer_efficiency_including_pow=li50,
        p90_logic_landauer_efficiency_including_pow=li90,
        p10_logic_landauer_efficiency_excluding_pow=le10,
        p50_logic_landauer_efficiency_excluding_pow=le50,
        p90_logic_landauer_efficiency_excluding_pow=le90,
        p50_logic_power_including_pow_w=lpi50,
        p50_logic_power_excluding_pow_w=lpe50,
        p50_wall_factor_above_landauer_including_pow=1.0 / ei50,
        p50_wall_factor_above_landauer_excluding_pow=1.0 / ee50,
        p50_logic_factor_above_landauer_including_pow=1.0 / li50,
        p50_logic_factor_above_landauer_excluding_pow=1.0 / le50,
        p50_pow_share_of_bitops=float(np.median(pow_bitops / np.maximum(bitops_incl, 1e-300))),
        p50_pow_share_of_power=float(np.median(pow_power / np.maximum(power_incl, 1e-300))),
    )
    return summary, category_rows


def write_csv(path: Path, rows: list[object]) -> None:
    if not rows:
        raise ValueError("no rows")
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(asdict(rows[0]).keys()))
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def make_plot(path: Path, summaries: list[YearSummary]) -> None:
    if plt is None:
        return
    # Keep this intentionally sparse; the CSV/JSON are the primary artifacts.
    years = np.array([s.year for s in sorted(summaries, key=lambda x: x.year)])
    bitops_incl = np.array([s.p50_bitops_including_pow for s in sorted(summaries, key=lambda x: x.year)])
    bitops_excl = np.array([s.p50_bitops_excluding_pow for s in sorted(summaries, key=lambda x: x.year)])
    eta_incl = np.array([s.p50_wall_landauer_efficiency_including_pow for s in sorted(summaries, key=lambda x: x.year)])
    eta_excl = np.array([s.p50_wall_landauer_efficiency_excluding_pow for s in sorted(summaries, key=lambda x: x.year)])

    fig = plt.figure(figsize=(9, 5.5))
    ax = fig.add_subplot(111)
    ax.plot(years, bitops_incl, marker="o", label="bitops/s incl. PoW")
    ax.plot(years, bitops_excl, marker="o", label="bitops/s excl. PoW")
    ax.set_yscale("log")
    ax.set_xlabel("Year")
    ax.set_ylabel("Functional bit operations per second")
    ax.set_title("Artificial computation on Earth, historical model")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path.with_name(path.stem + "_bitops.png"), dpi=180)
    plt.close(fig)

    fig = plt.figure(figsize=(9, 5.5))
    ax = fig.add_subplot(111)
    ax.plot(years, eta_incl, marker="o", label="Landauer efficiency incl. PoW")
    ax.plot(years, eta_excl, marker="o", label="Landauer efficiency excl. PoW")
    ax.set_yscale("log")
    ax.set_xlabel("Year")
    ax.set_ylabel("Wall Landauer efficiency")
    ax.set_title("Artificial computation vs. Landauer floor")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path.with_name(path.stem + "_landauer.png"), dpi=180)
    plt.close(fig)


def run(samples: int, seed: int, out_dir: Path) -> dict[str, object]:
    rng = np.random.default_rng(seed)
    summaries: list[YearSummary] = []
    categories: list[CategorySummary] = []
    for year in TARGET_YEARS:
        s, cats = sample_year(year, rng, samples)
        summaries.append(s)
        categories.extend(cats)

    out_dir.mkdir(parents=True, exist_ok=True)
    summary_csv = out_dir / "earth_artificial_bitops_historical_summary.csv"
    category_csv = out_dir / "earth_artificial_bitops_historical_categories.csv"
    json_path = out_dir / "earth_artificial_bitops_historical_estimate.json"
    plot_path = out_dir / "earth_artificial_bitops_historical_plot_base.png"
    write_csv(summary_csv, summaries)
    write_csv(category_csv, categories)
    make_plot(plot_path, summaries)

    payload = {
        "metric": "functional one-bit primitive operations per second",
        "landauer_formula": "eta_L = bitops_per_second * k_B * T * ln(2) / associated_power_watts",
        "temperature_k_quantiles": {"p10": 285.0, "p50": 300.0, "p90": 315.0},
        "samples": samples,
        "seed": seed,
        "target_years": TARGET_YEARS,
        "non_pow_anchors": {str(y): asdict(a) for y, a in NON_POW_ANCHORS.items()},
        "pow_anchors": {str(y): asdict(a) for y, a in POW_ANCHORS.items()},
        "summary": [asdict(s) for s in summaries],
        "categories": [asdict(c) for c in categories],
        "outputs": {
            "summary_csv": str(summary_csv),
            "category_csv": str(category_csv),
            "bitops_plot_png": str(plot_path.with_name(plot_path.stem + "_bitops.png")),
            "landauer_plot_png": str(plot_path.with_name(plot_path.stem + "_landauer.png")),
        },
    }
    json_path.write_text(json.dumps(payload, indent=2))
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=300_000)
    parser.add_argument("--seed", type=int, default=20260603)
    parser.add_argument("--out-dir", type=Path, default=Path("data/processed"))
    args = parser.parse_args()
    payload = run(args.samples, args.seed, args.out_dir)
    for row in payload["summary"]:
        print(
            f"{row['year']}: bitops incl={row['p50_bitops_including_pow']:.3e}, "
            f"excl={row['p50_bitops_excluding_pow']:.3e}, "
            f"eta_L incl={row['p50_wall_landauer_efficiency_including_pow']:.3e}, "
            f"excl={row['p50_wall_landauer_efficiency_excluding_pow']:.3e}"
        )


if __name__ == "__main__":
    main()
