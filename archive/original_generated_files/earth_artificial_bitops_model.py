#!/usr/bin/env python3
"""
earth_artificial_bitops_model.py

A first-pass Monte Carlo model for the rate of artificial computation on Earth,
measured as "functional 1-bit primitive operations per second."

Definition used here
--------------------
A bit operation is a low-level one-bit Boolean / adder-slice / multiply-partial
operation implied by a workload. This intentionally excludes:
  * cooling, displays, RF power, motors, and leakage/idle power that does not
    correspond to useful digital logic;
  * mere storage of bits;
  * most memory and interconnect bit motion, except insofar as it is folded into
    the coarse power-based estimates.

The main reason to keep this definition narrow is that it is refinable from
public anchors. A more physical "transistor switching events per second" model
would use different factors and likely different category rankings.

Run:
    python earth_artificial_bitops_model.py
    python earth_artificial_bitops_model.py --samples 1000000 --seed 7 --out-dir /tmp/bitops

The model is deliberately simple: each uncertain positive factor is represented
by p10 / p50 / p90 quantiles and sampled as a lognormal. The category total is
the product of its sampled factors. Edit BASELINE_CATEGORIES to refine it.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np


Z10 = 1.2815515655446004


@dataclass(frozen=True)
class Factor:
    """An uncertain positive factor represented by p10, p50, p90 quantiles."""

    name: str
    p10: float
    p50: float
    p90: float
    units: str = ""
    note: str = ""

    def sample(self, rng: np.random.Generator, n: int) -> np.ndarray:
        if self.p10 <= 0 or self.p50 <= 0 or self.p90 <= 0:
            raise ValueError(f"{self.name}: quantiles must be positive")
        if not (self.p10 <= self.p50 <= self.p90):
            raise ValueError(f"{self.name}: require p10 <= p50 <= p90")
        sigma = (math.log(self.p90) - math.log(self.p10)) / (2.0 * Z10)
        mu = math.log(self.p50)
        return rng.lognormal(mean=mu, sigma=sigma, size=n)


@dataclass(frozen=True)
class Category:
    """A product-form bitops category."""

    name: str
    factors: tuple[Factor, ...]
    include_in_no_pow: bool = True
    notes: str = ""

    def sample(self, rng: np.random.Generator, n: int) -> np.ndarray:
        x = np.ones(n, dtype=np.float64)
        for f in self.factors:
            x *= f.sample(rng, n)
        return x


BASELINE_CATEGORIES: tuple[Category, ...] = (
    Category(
        name="Bitcoin and other SHA-256 proof-of-work",
        include_in_no_pow=False,
        notes=(
            "hash_rate_hps is centered on ~0.98 ZH/s. bitops_per_hash is a "
            "low-level double-SHA-256 trial conversion; it is intentionally "
            "broad because ASIC-level gate sharing and the exact 'bit operation' "
            "definition matter."
        ),
        factors=(
            Factor("hash_rate_hps", 8.0e20, 9.8e20, 1.2e21, "hashes/s"),
            Factor("bitops_per_hash", 3.0e4, 1.0e5, 2.5e5, "bitops/hash"),
            Factor("other_sha256_pow_multiplier", 1.00, 1.03, 1.15, "x"),
        ),
    ),
    Category(
        name="AI accelerators in data centres",
        notes=(
            "Power is site/system-scale for accelerator installations, not just "
            "chip TDP. ops_per_joule_at_peak is tensor-op throughput efficiency; "
            "utilization discounts peak specs to average realized operation rate."
        ),
        factors=(
            Factor("site_power_w", 9.4e9, 2.3e10, 3.8e10, "W"),
            Factor("accelerator_fraction_of_site_power", 0.35, 0.55, 0.75, "x"),
            Factor("peak_accelerator_ops_per_joule", 1.5e12, 5.0e12, 1.0e13, "ops/J"),
            Factor("utilization_vs_peak", 0.08, 0.25, 0.50, "x"),
            Factor("bitops_per_accelerator_op", 16.0, 64.0, 192.0, "bitops/op"),
        ),
    ),
    Category(
        name="Conventional data-centre CPUs/GPUs/storage/networking",
        notes=(
            "A residual non-AI data-centre category. It converts facility power "
            "to IT power via PUE, applies a logic-compute fraction, then converts "
            "logic joules to one-bit primitive operations."
        ),
        factors=(
            Factor("site_power_w", 2.0e10, 3.5e10, 6.0e10, "W"),
            Factor("IT_fraction_from_PUE", 0.55, 0.65, 0.78, "x"),
            Factor("logic_compute_fraction_of_IT", 0.15, 0.35, 0.65, "x"),
            Factor("bitops_per_logic_joule", 3.0e11, 3.0e12, 2.0e13, "bitops/J"),
        ),
    ),
    Category(
        name="Telecom and data-transmission networks",
        notes=(
            "Network power is dominated by access and transmission infrastructure. "
            "Only the logic-processing fraction is counted as computation."
        ),
        factors=(
            Factor("network_power_w", 2.5e10, 3.3e10, 4.5e10, "W"),
            Factor("logic_fraction_of_network_power", 0.08, 0.20, 0.45, "x"),
            Factor("bitops_per_logic_joule", 2.0e11, 2.0e12, 1.5e13, "bitops/J"),
        ),
    ),
    Category(
        name="Phones, tablets, wearables",
        notes=(
            "Device count includes smartphones plus tablets/wearables. Average "
            "logic power is low because most devices are idle most of the day."
        ),
        factors=(
            Factor("active_devices", 4.8e9, 6.3e9, 7.8e9, "devices"),
            Factor("avg_logic_power_w", 0.02, 0.08, 0.35, "W/device"),
            Factor("bitops_per_logic_joule", 5.0e11, 5.0e12, 3.0e13, "bitops/J"),
        ),
    ),
    Category(
        name="Personal computers, workstations, consoles",
        notes=(
            "A broad installed-base category. Average logic power is averaged "
            "over wall-clock time, not just powered-on time."
        ),
        factors=(
            Factor("active_devices", 1.1e9, 1.7e9, 2.5e9, "devices"),
            Factor("avg_logic_power_w", 0.4, 2.5, 10.0, "W/device"),
            Factor("bitops_per_logic_joule", 2.0e11, 1.5e12, 8.0e12, "bitops/J"),
        ),
    ),
    Category(
        name="Consumer media electronics and cameras",
        notes=(
            "TVs, streaming boxes, set-top boxes, image pipelines, security cameras, "
            "and similar fixed-function media hardware."
        ),
        factors=(
            Factor("active_devices", 1.5e9, 2.5e9, 4.0e9, "devices"),
            Factor("avg_logic_power_w", 0.04, 0.20, 0.80, "W/device"),
            Factor("bitops_per_logic_joule", 2.0e11, 1.0e12, 6.0e12, "bitops/J"),
        ),
    ),
    Category(
        name="Embedded/IoT/automotive/industrial controllers",
        notes=(
            "A direct aggregate placeholder for MCUs, vehicles, appliances, industrial "
            "PLCs, sensors, payment terminals, building controls, etc. This is the "
            "least satisfying bucket and should be split in the next revision."
        ),
        factors=(
            Factor("aggregate_bitops_per_s", 1.0e19, 1.0e21, 1.0e23, "bitops/s"),
        ),
    ),
)


def summarize_samples(x: np.ndarray) -> dict[str, float]:
    return {
        "p05": float(np.quantile(x, 0.05)),
        "p10": float(np.quantile(x, 0.10)),
        "p50": float(np.quantile(x, 0.50)),
        "p90": float(np.quantile(x, 0.90)),
        "p95": float(np.quantile(x, 0.95)),
        "mean": float(np.mean(x)),
    }


def run_model(
    categories: Iterable[Category] = BASELINE_CATEGORIES,
    samples: int = 300_000,
    seed: int = 20260603,
) -> dict[str, object]:
    rng = np.random.default_rng(seed)
    category_samples: dict[str, np.ndarray] = {}
    category_meta: dict[str, Category] = {}

    for category in categories:
        category_samples[category.name] = category.sample(rng, samples)
        category_meta[category.name] = category

    total_including_pow = np.sum(list(category_samples.values()), axis=0)
    total_excluding_pow = np.sum(
        [s for name, s in category_samples.items() if category_meta[name].include_in_no_pow],
        axis=0,
    )

    rows = []
    median_sum = sum(float(np.median(s)) for s in category_samples.values())
    median_sum_no_pow = sum(
        float(np.median(s))
        for name, s in category_samples.items()
        if category_meta[name].include_in_no_pow
    )

    for name, s in category_samples.items():
        summary = summarize_samples(s)
        include = category_meta[name].include_in_no_pow
        rows.append(
            {
                "category": name,
                "include_in_no_pow": include,
                **summary,
                "share_of_median_sum_including_pow": summary["p50"] / median_sum,
                "share_of_median_sum_excluding_pow": (
                    summary["p50"] / median_sum_no_pow if include else None
                ),
                "notes": category_meta[name].notes,
            }
        )

    rows.sort(key=lambda r: r["p50"], reverse=True)

    return {
        "definition": "functional one-bit primitive operations per second",
        "samples": samples,
        "seed": seed,
        "categories": rows,
        "total_including_pow": summarize_samples(total_including_pow),
        "total_excluding_pow": summarize_samples(total_excluding_pow),
    }


def sci(x: float | None) -> str:
    if x is None:
        return ""
    if x == 0:
        return "0"
    return f"{x:.3e}"


def print_report(result: dict[str, object]) -> None:
    print(f"Definition: {result['definition']}")
    print(f"Samples: {result['samples']:,}   seed: {result['seed']}")
    print()
    print("Category estimates, bitops/s")
    cols = ("category", "p10", "p50", "p90", "share_of_median_sum_including_pow")
    print(f"{cols[0]:62s} {cols[1]:>12s} {cols[2]:>12s} {cols[3]:>12s} {'share incl PoW':>14s}")
    print("-" * 118)
    for row in result["categories"]:  # type: ignore[index]
        print(
            f"{row['category'][:62]:62s} "
            f"{sci(row['p10']):>12s} {sci(row['p50']):>12s} {sci(row['p90']):>12s} "
            f"{row['share_of_median_sum_including_pow']:14.3%}"
        )

    print()
    print("Totals")
    for name in ("total_including_pow", "total_excluding_pow"):
        s = result[name]  # type: ignore[index]
        print(
            f"{name:22s}: p10={sci(s['p10'])}  p50={sci(s['p50'])}  "
            f"p90={sci(s['p90'])}  mean={sci(s['mean'])}"
        )


def write_outputs(result: dict[str, object], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "earth_artificial_bitops_current_estimate.json"
    csv_path = out_dir / "earth_artificial_bitops_current_estimate.csv"

    json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    rows = result["categories"]  # type: ignore[index]
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "category",
            "include_in_no_pow",
            "p05",
            "p10",
            "p50",
            "p90",
            "p95",
            "mean",
            "share_of_median_sum_including_pow",
            "share_of_median_sum_excluding_pow",
            "notes",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print()
    print(f"Wrote {json_path}")
    print(f"Wrote {csv_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=300_000)
    parser.add_argument("--seed", type=int, default=20260603)
    parser.add_argument("--out-dir", type=Path, default=None)
    args = parser.parse_args()

    result = run_model(samples=args.samples, seed=args.seed)
    print_report(result)
    if args.out_dir is not None:
        write_outputs(result, args.out_dir)


if __name__ == "__main__":
    main()
