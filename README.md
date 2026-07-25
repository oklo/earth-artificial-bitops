# Earth Artificial Bit Operations

This repository estimates artificial computation on Earth over time, expresses the result as functional one-bit primitive operations per second, converts those estimates to a Landauer-efficiency yardstick, and explores when irreversible computing could become a macroscopic energy constraint if reversible computing is not available at scale.

## Headline Results

- Current inclusive artificial computation: approximately `1.0 x 10^26` bitops/s, including SHA-256 proof-of-work.
- Current diagnostic non-PoW estimate: approximately `1.0 x 10^24` bitops/s.
- Current wall-power Landauer efficiency: approximately `1.6 x 10^-6` including PoW and `2.4 x 10^-8` excluding PoW.
- Central declining-growth energy crossing: current global primary-energy scale around `2090`, current Earth-intercepted solar power around `2170`, and solar luminosity around `2473`.
- Constant 50%/yr bitops-demand sensitivity: current global primary-energy scale around `2065`, current Earth-intercepted solar power around `2089`, and solar luminosity around `2142`.

## Reproduce

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
make all PYTHON=python
```

The Monte Carlo components use fixed seeds and stable output filenames.  Generated CSV/JSON outputs are written to `data/processed/`; figures are written to `figures/`.

## Model Definition

A bitop means a functional one-bit primitive operation implied by a workload: Boolean operations, one-bit adder slices, or multiply partial products.  It is not a FLOP, instruction, transistor-switching event, or data-movement bit.

Landauer efficiency is defined as:

```text
eta_L = N_bitop k_B T ln(2) / P_wall
```

with `T = 300 K` unless otherwise noted.  This is a thermodynamic yardstick for comparing computation to the irreversible bit-erasure floor, not a literal entropy-production audit.

## Caveats

- SHA-256 proof-of-work dominates the inclusive bitops estimate after the mid-2010s.  It is included because the accounting exercise is all artificial computation.
- A non-PoW estimate is retained as a diagnostic, but the talk-facing historical table uses the inclusive estimate.
- Future extrapolations are sensitivity analyses, not forecasts.
- The energy-threshold calculations explicitly exclude the possibility that reversible computing becomes economically and technically available at scale.
- The 2025 table row is reconstructed/estimated from current data, not a future extrapolation.  The 2030 and 2035 rows are forward extrapolations of aggregate bitops history and are not assigned to a detailed technology stack.

## File Guide

- `src/earth_bitops/` contains the current, historical, future, plotting, and table-generation code.
- `scripts/` contains repo-root entry points used by the Makefile.
- `data/processed/` contains generated CSV/JSON/Markdown tables.
- `figures/` contains generated PNG/SVG figures used in the talk.
- `docs/` contains methodology, assumptions, source notes, and future-interpretation text.
- `archive/original_generated_files/` preserves the original flat generated files from the prior analysis bundle.
