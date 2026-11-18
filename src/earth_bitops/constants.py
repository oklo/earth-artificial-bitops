"""Physical constants, reference thresholds, and world population.

Only physical/reference inputs live here.  Model outputs (current bitops,
efficiencies, powers) are read from the generated files in data/processed/.
"""

from __future__ import annotations

import math

BOLTZMANN_J_PER_K = 1.380_649e-23
TEMPERATURE_K = 300.0
LN2 = math.log(2.0)
LANDAUER_J_PER_BIT_300K = BOLTZMANN_J_PER_K * TEMPERATURE_K * LN2

SECONDS_PER_JULIAN_YEAR = 365.25 * 24.0 * 3600.0

# IEA Global Energy Review 2026: ~+8 EJ (+1.3%) in 2025 => ~630 EJ/yr.
GLOBAL_PRIMARY_ENERGY_EJ_PER_YR = 630.0
CURRENT_GLOBAL_PRIMARY_ENERGY_W = GLOBAL_PRIMARY_ENERGY_EJ_PER_YR * 1e18 / SECONDS_PER_JULIAN_YEAR
# Long-run growth of world primary energy, used for the "moving target" variant.
GLOBAL_PRIMARY_ENERGY_GROWTH = 0.015

EARTH_INTERCEPTED_SOLAR_W = 1.74e17          # S * pi * R_earth^2, S = 1361 W/m^2
EARTH_ABSORBED_SOLAR_W = 0.70 * EARTH_INTERCEPTED_SOLAR_W   # Bond albedo ~0.30
# Waste heat equal to 1% of absorbed sunlight (~2.4 W/m^2 globally averaged),
# comparable to present anthropogenic greenhouse forcing.
WASTE_HEAT_CLIMATE_W = 0.01 * EARTH_ABSORBED_SOLAR_W
SOLAR_LUMINOSITY_W = 3.828e26                # IAU 2015 nominal

THRESHOLDS = {
    "current_global_primary_energy": CURRENT_GLOBAL_PRIMARY_ENERGY_W,
    "waste_heat_1pct_absorbed_solar": WASTE_HEAT_CLIMATE_W,
    "earth_intercepted_solar_power": EARTH_INTERCEPTED_SOLAR_W,
    "solar_luminosity": SOLAR_LUMINOSITY_W,
}

# World population (UN WPP 2024, medium variant for future years), persons.
WORLD_POPULATION = {
    1940: 2.30e9, 1945: 2.38e9, 1950: 2.49e9, 1960: 3.02e9, 1970: 3.69e9,
    1980: 4.44e9, 1990: 5.32e9, 1995: 5.74e9, 2000: 6.15e9, 2005: 6.56e9,
    2010: 6.99e9, 2015: 7.43e9, 2020: 7.84e9, 2025: 8.23e9, 2026: 8.30e9,
    2030: 8.57e9, 2035: 8.89e9, 2040: 9.18e9, 2050: 9.66e9,
}
