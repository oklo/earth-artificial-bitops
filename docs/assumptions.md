# Assumptions

- Temperature for the Landauer yardstick is `T = 300 K` throughout, including the long-run thresholds.
- Inclusive artificial computation includes SHA-256 proof-of-work; non-PoW values are always reported alongside, and trend fits use the non-PoW series.
- Historical p50 values are order-of-magnitude anchors with deliberately broad uncertainty. 1945 is the geometric mean of the 1940 and 1950 anchors; 2025 is interpolated between 2020 and 2026 with its own proof-of-work anchor.
- 2026 proof-of-work: about 0.98 ZH/s, 21 J/TH fleet efficiency, 10^5 bitops per hash (adder-slice convention).
- 2026-2035 projection (annual factors, p10/p50/p90): hashrate 0.97/1.08/1.20; J/TH 0.86/0.90/0.95; AI power 1.15/1.25/1.38; AI bitops per joule 1.15/1.30/1.45; other power 1.00/1.03/1.06; other bitops per joule 1.15/1.25/1.35. AI average draw in 2026 is 23 GW (16-32 GW).
- Long-run scenarios: non-PoW bitops and efficiency follow least-squares log-linear trends fitted to the historical p50 series (1945-2026, and 2000-2026 as a check); efficiency stops at a ceiling `eta_max` of 10^-3, 10^-2, or 1; proof-of-work is held at its 2026 level.
- World primary energy reference: 630 EJ/yr (20 TW). A variant with the reference growing 1.5%/yr is also reported.
