# When does computation become energy-dominant, and when does reversible computing matter?

The energy equation is

```text
P = N_bitop kT ln(2) / eta_L
```

For 80 years demand (N) has grown about 62%/yr while efficiency (eta_L) improved about 44%/yr, so power grew only about 12%/yr. That balance cannot continue for irreversible logic: reliable irreversible operations need tens of kT each, so eta_L has a ceiling near 10^-2 at the device level and lower at the wall. At the historical rate, non-PoW eta_L (2.6 x 10^-8 in 2026) reaches 10^-3 around 2055, 10^-2 around 2061, and the Landauer limit itself around 2074.

Once the ceiling is reached, every further doubling of computation needs a doubling of power. If demand keeps its trend, power growth jumps from about 12%/yr to about 60%/yr, and the thresholds fall in quick succession:

| Threshold | Irreversible, eta_max 10^-3 / 10^-2 / 1 | Power trend continues (needs reversible) |
| --- | ---: | ---: |
| World primary energy | 2059 / 2063 / 2070 | 2070 |
| 1% of absorbed sunlight | 2067 / 2072 / 2081 | 2106 |
| Earth-intercepted sunlight | 2077 / 2082 / 2092 | 2150 |
| Solar luminosity | 2122 / 2127 / 2136 | 2339 |

Reading the table:

- The world-primary-energy crossing barely depends on the ceiling, because by the time any ceiling binds, power is already within a factor of a few of 20 TW on the 12%/yr trend alone. "Around 2060-2070" is the robust statement.
- Reversible computing becomes economically decisive at the ceiling, about 2055-2075, not at some distant date. The power-trend column is what the same demand costs if efficiency keeps improving; it requires eta_L of about 10 by 2080 and about 10^4 by 2100, i.e. dissipation far below kT ln 2 per bitop.
- The 1%-of-absorbed-sunlight row is the practical Earth limit: waste heat of about 2.4 W/m^2 is comparable to present greenhouse forcing. Earth-intercepted sunlight and solar luminosity are scale markers (Kardashev I and II); they imply off-planet computing with different radiator temperatures.

These are conditional statements about trends, not forecasts. The slower-demand sensitivity in `data/processed/earth_artificial_bitops_future_summary.md` shows the same qualitative result with later dates (for +30%/yr demand: world primary energy 2085-2112).
