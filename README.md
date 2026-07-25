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

All sources are included. 2025 is reconstructed from the fitted/current model; 2030 and 2035 are forward extrapolations.

| Year | Bitops/sec | Avg. Landauer eta_L | Bitops/person/year | Energy/person/year | Primary contributor/year |
| ---: | ---: | ---: | ---: | ---: | --- |
| 1940 | `3.98 x 10^6` | `1.14 x 10^-21` | `5.46 x 10^4` | `0.038 kWh` | Punched-card, relay, electromechanical, analog |
| 1950 | `3.01 x 10^8` | `4.35 x 10^-20` | `3.81 x 10^6` | `0.070 kWh` | Early electronic + electromechanical business machines |
| 1960 | `3.02 x 10^10` | `4.32 x 10^-19` | `3.16 x 10^8` | `0.582 kWh` | Commercial/scientific computers |
| 1970 | `2.98 x 10^12` | `8.61 x 10^-18` | `2.55 x 10^10` | `2.36 kWh` | Mainframes, minis, early IC systems |
| 1980 | `2.99 x 10^14` | `2.87 x 10^-16` | `2.12 x 10^12` | `5.91 kWh` | Embedded / app-specific logic; mainframes/minis; PCs/consoles |
| 1990 | `2.98 x 10^16` | `8.57 x 10^-15` | `1.76 x 10^14` | `16.4 kWh` | Embedded / app-specific logic; PCs/workstations; servers/mainframes |
| 1995 | `4.96 x 10^17` | `9.52 x 10^-14` | `2.72 x 10^15` | `22.7 kWh` | Embedded / app-specific logic; PCs/consoles; servers/data centres |
| 2000 | `1.15 x 10^19` | `1.37 x 10^-12` | `5.87 x 10^16` | `34.1 kWh` | Embedded logic; PCs/consoles; servers/data centres; telecom/mobile |
| 2005 | `3.00 x 10^20` | `1.96 x 10^-11` | `1.44 x 10^18` | `58.6 kWh` | Embedded logic; PCs/consoles; telecom; servers/data centres; mobile |
| 2010 | `2.50 x 10^21` | `1.20 x 10^-10` | `1.12 x 10^19` | `74.8 kWh` | Embedded logic; PCs/consoles; phones/tablets; telecom/consumer media |
| 2015 | `7.25 x 10^22` | `2.96 x 10^-9` | `3.06 x 10^20` | `82.5 kWh` | SHA-256 PoW; embedded logic; AI/deep-learning GPUs |
| 2020 | `1.29 x 10^25` | `3.88 x 10^-7` | `5.15 x 10^22` | `106 kWh` | SHA-256 PoW dominates; AI accelerators; embedded logic |
| 2025 | `7.90 x 10^25` | `1.40 x 10^-6` | `3.03 x 10^23` | `173 kWh` | 2025 estimate; SHA-256 PoW still dominant; AI accelerators rising |
| 2030 | `1.89 x 10^27` | `2.29 x 10^-5` | `6.95 x 10^24` | `242 kWh` | Extrapolated; likely SHA-256 PoW + AI/accelerator-scale compute |
| 2035 | `4.51 x 10^28` | `3.76 x 10^-4` | `1.60 x 10^26` | `340 kWh` | Extrapolated; high-throughput ASIC/accelerator compute likely dominant |

`eta_L = N_bitop kT ln(2) / P_wall` at `T = 300 K`. Energy/person/year is annual wall energy for artificial computation divided by world population.

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
