#!/usr/bin/env python3
"""Independent sanity checks used in docs/review_2026-11-11.md.

Standard library only.  Nothing here reads or writes repository outputs; it
recomputes the quantities the review relies on so they can be audited.

    python scripts/review_independent_checks.py
"""

from __future__ import annotations

import math

K_B = 1.380649e-23
T = 300.0
E_L = K_B * T * math.log(2.0)  # J per bit erasure at 300 K
YEAR_S = 365.25 * 86400.0


def sha256_bitops_per_trial(adder_cost: float, compressions: float = 1.9) -> float:
    """One-bit primitive ops for a double-SHA-256 nonce trial.

    adder_cost = cost of one 1-bit full-adder slice (1 = adder-slice convention,
    ~5 = two-input gate convention).  Per round: Sigma0, Sigma1 (2 XOR/bit each),
    Ch (~3 gates/bit), Maj (~4 gates/bit), 7 x 32-bit additions.  Message
    schedule: 48 words x (sigma0, sigma1, 3 additions).  Mining with a midstate
    costs ~1.9 compressions per trial.
    """
    rnd = 64 + 64 + 96 + 128 + 7 * 32 * adder_cost
    sched = 48 * (64 + 64 + 3 * 32 * adder_cost)
    final = 8 * 32 * adder_cost
    return compressions * (64 * rnd + sched + final)


def main() -> None:
    print(f"k_B T ln2 (300 K) = {E_L:.4e} J")

    print("\n[1] SHA-256 bitops per nonce trial")
    for label, cost in (("adder-slice = 1 bitop", 1.0), ("full adder = 5 gate ops", 5.0)):
        print(f"  {label:26s}: {sha256_bitops_per_trial(cost):.2e}")

    print("\n[2] Proof-of-work Landauer efficiency (1.0 ZH/s, 8% site overhead)")
    for j_per_th in (20.0, 25.0):
        power = 1.0e21 / 1e12 * j_per_th * 1.08
        for bph in (1.0e5, 2.4e5):
            n = 1.0e21 * bph
            print(f"  {j_per_th:4.0f} J/TH, {bph:.1e} bitops/hash: P={power/1e9:5.1f} GW "
                  f"N={n:.2e} eta_L={n*E_L/power:.2e}")

    print("\n[3] AI accelerators bottom-up (H100e at 8-bit dense peak 1.98e15 op/s)")
    for stock in (2.0e7, 3.2e7, 4.6e7):
        vals = [stock * 1.98e15 * u * b for u in (0.15, 0.30) for b in (20, 40)]
        print(f"  stock {stock:.1e} H100e: N = {min(vals):.1e} .. {max(vals):.1e} bitops/s")
    print(f"  eta_L for 1e24 bitops/s at 30 GW: {1e24*E_L/30e9:.1e}")
    print(f"  bitops/s per GW: PoW {1e26/22:.1e} vs AI {1e24/30:.1e}")

    print("\n[4] Talk-table implied growth")
    for a, b in ((7.9e25, 1.89e27), (1.89e27, 4.51e28)):
        print(f"  {a:.2e} -> {b:.2e} over 5 yr: {((b/a)**0.2-1)*100:.1f}%/yr")

    print("\n[5] Two-component projection (non-PoW from 1.35e24, PoW from 1.0e26 at +10%/yr)")
    for g_ai in (1.8, 2.5, 3.2):
        for year in (2030, 2035):
            t = year - 2026
            n_ai, n_pow = 1.35e24 * g_ai**t, 1.0e26 * 1.1**t
            print(f"  non-PoW x{g_ai}/yr {year}: non-PoW {n_ai:.1e} PoW {n_pow:.1e} total {n_ai+n_pow:.1e}")

    print("\n[6] Crossing years: N0 = 1.04e26 in 2026, constant growth, fixed system eta_L")
    thresholds = {
        "global primary (630 EJ/yr)": 630e18 / YEAR_S,
        "1% absorbed solar": 1.2e15,
        "Earth-intercepted solar": 1.74e17,
        "solar luminosity": 3.828e26,
    }
    print("  columns: " + " | ".join(thresholds))
    for g in (0.20, 0.30, 0.50, 0.88):
        for eta in (1.0, 1e-2, 1e-3):
            years = []
            for p in thresholds.values():
                n_req = p * eta / E_L
                years.append(2026 + math.log(n_req / 1.04e26) / math.log(1 + g))
            print(f"  g={g:.2f} eta={eta:<6g}: " + "  ".join(f"{y:.0f}" for y in years))

    print("\n[7] Reliability ceiling on irreversible logic (p_err ~ exp(-E/kT))")
    for p in (1e-15, 1e-20, 1e-25):
        e = -math.log(p)
        print(f"  p_err={p:g}: E >= {e:.0f} kT -> device eta_L <= {math.log(2)/e:.3f}")

    print("\n[8] Waste-heat forcing (Earth area 5.1e14 m2, absorbed solar 1.22e17 W, no feedbacks)")
    for p in (2.0e13, 1.2e15, 1.74e17):
        dt = 255.0 * ((1 + p / 1.22e17) ** 0.25 - 1)
        print(f"  P={p:.1e} W: {p/5.1e14:7.2f} W/m2, dT_eff ~ {dt:.2f} K")


if __name__ == "__main__":
    main()
