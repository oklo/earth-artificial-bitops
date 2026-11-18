"""Near-term (2026-2035) component projection of artificial bitops and power.

Three components are carried separately because they have very different
bitops-per-joule and very different growth drivers:

  * SHA-256 proof-of-work: bitops = hashrate x bitops/hash; power = hashrate x J/TH.
  * AI accelerators: bitops = power x bitops/J.  Power growth is anchored on the
    IEA base case (AI-focused data centres 155 TWh in 2025 -> ~465 TWh in 2030,
    about +25%/yr).  bitops/J growth is hardware op/J growth (~1.4x/yr) reduced
    by the move to lower-precision arithmetic (fewer bitops per op).
  * Other non-PoW computation: slow power growth, Koomey-like bitops/J growth.

The 2026 starting point is sampled from the same anchors as the historical
model, so the 2026 projection row reproduces the 2026 historical row.

Every uncertain growth rate is a p10/p50/p90 lognormal on the annual factor,
sampled once per Monte Carlo draw and held for the whole decade.
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from earth_bitops.constants import LANDAUER_J_PER_BIT_300K
from earth_bitops.historical_model import NON_POW_ANCHORS, POW_ANCHORS, LogQuantile

BASE_YEAR = 2026
END_YEAR = 2035

# Annual multiplicative factors (p10, p50, p90).
GROWTH = {
    "pow_hashrate": LogQuantile(0.97, 1.08, 1.20),       # flat-to-declining since 2025; 2028 halving
    "pow_j_per_th": LogQuantile(0.86, 0.90, 0.95),       # fleet ~21 J/TH now, frontier ~9.5 J/TH
    "ai_power": LogQuantile(1.15, 1.25, 1.38),           # IEA base case ~+25%/yr to 2030
    "ai_bitops_per_joule": LogQuantile(1.15, 1.30, 1.45),
    "other_power": LogQuantile(1.00, 1.03, 1.06),
    "other_bitops_per_joule": LogQuantile(1.15, 1.25, 1.35),
}
# 2026 split of the non-PoW anchor.
AI_SHARE_OF_NONPOW_BITOPS = (0.85, 0.99)                 # uniform; current model median ~0.95
AI_POWER_W_2026 = LogQuantile(1.6e10, 2.3e10, 3.2e10)    # average draw; IEA 155 TWh (2025) x ~1.3


def _q(x: np.ndarray) -> tuple[float, float, float]:
    p10, p50, p90 = np.quantile(x, [0.10, 0.50, 0.90])
    return float(p10), float(p50), float(p90)


def run(out_data: Path, samples: int = 200_000, seed: int = 20261111) -> list[dict[str, float]]:
    rng = np.random.default_rng(seed)
    n = samples
    e_l = LANDAUER_J_PER_BIT_300K

    pw = POW_ANCHORS[BASE_YEAR]
    h0 = pw.hash_rate_hps.sample(rng, n)
    bph = pw.bitops_per_hash.sample(rng, n)
    other_mult = pw.other_sha256_multiplier.sample(rng, n)
    jth0 = pw.fleet_efficiency_j_per_th.sample(rng, n)
    overhead = pw.site_overhead_multiplier.sample(rng, n)

    npw = NON_POW_ANCHORS[BASE_YEAR]
    nonpow_n0 = npw.bitops.sample(rng, n)
    nonpow_p0 = npw.associated_power_w.sample(rng, n)
    ai_share = rng.uniform(*AI_SHARE_OF_NONPOW_BITOPS, size=n)
    ai_n0 = nonpow_n0 * ai_share
    other_n0 = nonpow_n0 - ai_n0
    ai_p0 = np.minimum(AI_POWER_W_2026.sample(rng, n), 0.5 * nonpow_p0)
    other_p0 = nonpow_p0 - ai_p0

    g = {k: v.sample(rng, n) for k, v in GROWTH.items()}

    rows: list[dict[str, float]] = []
    for year in range(BASE_YEAR, END_YEAR + 1):
        t = year - BASE_YEAR
        h = h0 * g["pow_hashrate"] ** t
        pow_n = h * bph * other_mult
        pow_p = h / 1e12 * jth0 * g["pow_j_per_th"] ** t * other_mult * overhead
        ai_p = ai_p0 * g["ai_power"] ** t
        ai_n = ai_n0 * (g["ai_power"] * g["ai_bitops_per_joule"]) ** t
        other_p = other_p0 * g["other_power"] ** t
        other_n = other_n0 * (g["other_power"] * g["other_bitops_per_joule"]) ** t

        nonpow_n, nonpow_p = ai_n + other_n, ai_p + other_p
        total_n, total_p = nonpow_n + pow_n, nonpow_p + pow_p
        series = {
            "bitops_including_pow": total_n,
            "bitops_excluding_pow": nonpow_n,
            "bitops_pow": pow_n,
            "bitops_ai": ai_n,
            "bitops_other": other_n,
            "power_including_pow_w": total_p,
            "power_excluding_pow_w": nonpow_p,
            "power_pow_w": pow_p,
            "power_ai_w": ai_p,
            "power_other_w": other_p,
            "eta_including_pow": total_n * e_l / total_p,
            "eta_excluding_pow": nonpow_n * e_l / nonpow_p,
            "eta_pow": pow_n * e_l / pow_p,
            "eta_ai": ai_n * e_l / ai_p,
            "hashrate_hps": h,
        }
        row: dict[str, float] = {"year": year}
        for name, x in series.items():
            for tag, val in zip(("p10", "p50", "p90"), _q(x)):
                row[f"{tag}_{name}"] = val
        row["prob_ai_bitops_exceed_pow"] = float(np.mean(ai_n > pow_n))
        rows.append(row)

    out_data.mkdir(parents=True, exist_ok=True)
    with (out_data / "earth_artificial_bitops_projection_2026_2035.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    with (out_data / "earth_artificial_bitops_projection_assumptions.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["annual_factor", "p10", "p50", "p90"])
        for k, v in GROWTH.items():
            writer.writerow([k, v.p10, v.p50, v.p90])
    return rows
