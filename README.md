# Earth Artificial Bit Operations

This repository estimates artificial computation on Earth over time, expresses the result as functional one-bit primitive operations per second, converts those estimates to a Landauer-efficiency yardstick, and explores when irreversible computing could become a macroscopic energy constraint if reversible computing is not available at scale.

## Headline Results

- Current inclusive artificial computation: approximately `1.0 x 10^26` bitops/s, including SHA-256 proof-of-work.
- Current diagnostic non-PoW estimate: approximately `1.0 x 10^24` bitops/s.
- Current wall-power Landauer efficiency: approximately `1.6 x 10^-6` including PoW and `2.4 x 10^-8` excluding PoW.
- Central declining-growth energy crossing: current global primary-energy scale around `2090`, current Earth-intercepted solar power around `2170`, and solar luminosity around `2473`.
- Constant 50%/yr bitops-demand sensitivity: current global primary-energy scale around `2065`, current Earth-intercepted solar power around `2089`, and solar luminosity around `2142`.

| Quantity | Inclusive / central value | Notes |
| --- | ---: | --- |
| Current artificial computation | `1.04 x 10^26` bitops/s | Includes SHA-256 proof-of-work |
| Current non-PoW diagnostic | `1.35 x 10^24` bitops/s | Excludes proof-of-work |
| Current wall-power Landauer efficiency | `1.63 x 10^-6` | Inclusive estimate at 300 K |
| Current non-PoW Landauer efficiency | `2.56 x 10^-8` | Diagnostic estimate at 300 K |
| Central global-energy crossing | `2090` | Current global primary-energy scale |
| Central Earth-insolation crossing | `2170` | Current Earth-intercepted solar power |
| Central solar-luminosity crossing | `2473` | Civilization-scale reference marker |
| Constant 50%/yr global-energy crossing | `2065` | Sensitivity, not forecast |
| Constant 50%/yr Earth-insolation crossing | `2089` | Sensitivity, not forecast |
| Constant 50%/yr solar-luminosity crossing | `2142` | Sensitivity, not forecast |

## Talk Table

| Year | Inclusive artificial bitops/s | Status | Contributor note |
| ---: | ---: | --- | --- |
| 1940 | `3.90 x 10^6` | reconstructed / estimated | relay/electromechanical and special-purpose machines |
| 1950 | `3.00 x 10^8` | reconstructed / estimated | early stored-program electronic computers |
| 1960 | `3.00 x 10^10` | reconstructed / estimated | mainframes and military/scientific systems |
| 1970 | `3.00 x 10^12` | reconstructed / estimated | mainframes, minicomputers, early embedded control |
| 1980 | `3.00 x 10^14` | reconstructed / estimated | microprocessors, minicomputers, early PCs |
| 1990 | `3.00 x 10^16` | reconstructed / estimated | PCs, workstations, mainframes, embedded systems |
| 1995 | `5.00 x 10^17` | reconstructed / estimated | internet-era PCs and servers |
| 2000 | `1.10 x 10^19` | reconstructed / estimated | PC/web era plus data centres |
| 2005 | `3.00 x 10^20` | reconstructed / estimated | cloud, GPUs, mobile ramp |
| 2010 | `2.50 x 10^21` | reconstructed / estimated | smartphones, cloud, early PoW |
| 2015 | `7.30 x 10^22` | reconstructed / estimated | cloud plus SHA-256 PoW |
| 2020 | `1.30 x 10^25` | reconstructed / estimated | SHA-256 PoW with cloud/accelerator growth |
| 2025 | `7.90 x 10^25` | reconstructed / estimated | estimated current/reconstructed row; SHA-256 PoW plus accelerator-scale compute |
| 2030 | `1.90 x 10^27` | forward extrapolation | qualitative: likely SHA-256 PoW plus AI/accelerator-scale compute |
| 2035 | `4.50 x 10^28` | forward extrapolation | qualitative forward extrapolation of aggregate bitops |

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
