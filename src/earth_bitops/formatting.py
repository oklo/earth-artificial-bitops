"""Formatting helpers for tables and documentation outputs."""

from __future__ import annotations

import math


def sci_tex(value: float, digits: int = 2) -> str:
    """Return compact scientific notation for Markdown text."""
    if value == 0:
        return "0"
    exponent = math.floor(math.log10(abs(value)))
    mantissa = value / 10**exponent
    return f"{mantissa:.{digits}f} x 10^{exponent}"


def source_label(year: int) -> str:
    if year <= 2025:
        return "reconstructed / estimated"
    return "forward extrapolation"
