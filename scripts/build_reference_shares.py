#!/usr/bin/env python3
"""Build data/reference/historical_nonpow_group_shares.csv.

The original analysis bundle shipped a category-resolved history
(archive/original_generated_files/earth_artificial_bitops_historical_categories.csv)
but not the code that produced it.  That file is treated here as reference
data: only the *shares* of non-PoW bitops by display group are kept, and they
are applied to the non-PoW totals produced by the current historical model.

Years missing from the archive (1945, 2025) are log-interpolated between
neighbours and renormalized.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from earth_bitops.plotting import GROUP_ORDER, group_category

ARCHIVE = Path("archive/original_generated_files/earth_artificial_bitops_historical_categories.csv")
OUT = Path("data/reference/historical_nonpow_group_shares.csv")
EXTRA_YEARS = (1945, 2025)
FLOOR = 1e-12


def main() -> None:
    cats = pd.read_csv(ARCHIVE)
    cats = cats[cats["include_in_no_pow"].astype(bool)].copy()
    cats["group"] = cats["category"].map(group_category)
    table = cats.pivot_table(index="year", columns="group", values="bitops_p50", aggfunc="sum").fillna(0.0)
    groups = [g for g in GROUP_ORDER if g != "SHA-256 proof-of-work"]
    table = table.reindex(columns=groups, fill_value=0.0)
    shares = table.div(table.sum(axis=1), axis=0)
    for year in EXTRA_YEARS:
        lo = max(y for y in shares.index if y < year)
        hi = min(y for y in shares.index if y > year)
        w = (year - lo) / (hi - lo)
        a, b = shares.loc[lo].to_numpy(), shares.loc[hi].to_numpy()
        mix = np.exp((1 - w) * np.log(np.maximum(a, FLOOR)) + w * np.log(np.maximum(b, FLOOR)))
        mix[(a == 0) & (b == 0)] = 0.0
        shares.loc[year] = mix / mix.sum()
    shares = shares.sort_index()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    long = shares.reset_index().melt(id_vars="year", var_name="group", value_name="share_of_nonpow_bitops")
    long = long[long["share_of_nonpow_bitops"] > 0].sort_values(["year", "group"])
    long.to_csv(OUT, index=False)
    print(f"Wrote {OUT} ({len(long)} rows)")


if __name__ == "__main__":
    main()
