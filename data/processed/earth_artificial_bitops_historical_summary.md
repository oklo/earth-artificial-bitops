# Historical artificial computation and Landauer efficiency

Monte Carlo p50 values from the updated model. Full p10/p50/p90 values are in the CSV and JSON outputs. The 2026 row is included for continuity with the current-day point estimate; the requested historical rows are 1940–2020.

| Year | bitops/s excl. PoW | bitops/s incl. PoW | wall eta_L excl. PoW | wall eta_L incl. PoW | PoW share of bitops |
|---:|---:|---:|---:|---:|---:|
| 2026 | 1.352e+24 | 1.040e+26 | 2.557e-08 | 1.633e-06 | 0.987 |
| 2020 | 8.018e+22 | 1.288e+25 | 2.713e-09 | 3.876e-07 | 0.994 |
| 2015 | 1.505e+22 | 7.251e+22 | 6.153e-10 | 2.960e-09 | 0.741 |
| 2010 | 2.497e+21 | 2.497e+21 | 1.196e-10 | 1.196e-10 | 0.000 |
| 2005 | 2.998e+20 | 2.998e+20 | 1.955e-11 | 1.955e-11 | 0.000 |
| 2000 | 1.147e+19 | 1.147e+19 | 1.371e-12 | 1.371e-12 | 0.000 |
| 1995 | 4.957e+17 | 4.957e+17 | 9.524e-14 | 9.524e-14 | 0.000 |
| 1990 | 2.977e+16 | 2.977e+16 | 8.570e-15 | 8.570e-15 | 0.000 |
| 1980 | 2.994e+14 | 2.994e+14 | 2.867e-16 | 2.867e-16 | 0.000 |
| 1970 | 2.985e+12 | 2.985e+12 | 8.611e-18 | 8.611e-18 | 0.000 |
| 1960 | 3.016e+10 | 3.016e+10 | 4.321e-19 | 4.321e-19 | 0.000 |
| 1950 | 3.013e+08 | 3.013e+08 | 4.348e-20 | 4.348e-20 | 0.000 |
| 1940 | 3.982e+06 | 3.982e+06 | 1.141e-21 | 1.141e-21 | 0.000 |

## Interpretation

- The numerator is functional one-bit primitive operations per second, not transistor switches, memory movement, instructions/s, FLOP/s, storage capacity, or communication bits transmitted.
- The wall Landauer efficiency uses associated system/wall power. Logic-only Landauer efficiency columns are also in the CSV/JSON.
- Before 1980, p50 values should be treated as order-of-magnitude anchors; the uncertainty bands are intentionally very broad.
- After 2015, the inclusive series is dominated by SHA-256 proof-of-work. The excluding-PoW series is dominated increasingly by AI/data-centre accelerators.