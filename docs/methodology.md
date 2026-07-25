# Methodology

The numerator is functional artificial computation on Earth measured in one-bit primitive operations per second.  This deliberately excludes storage capacity, most bit motion, displays, cooling, motors, and idle/leakage power unless those costs are folded into a coarse wall-power estimate.

The current-day model is a product-form Monte Carlo estimate across broad categories: SHA-256 proof-of-work, AI accelerators, conventional data-centre computation, telecom/network logic, phones/tablets/wearables, PCs/workstations/consoles, consumer media electronics, and embedded/industrial controllers.

The historical model uses broad log-quantile anchors by year.  Before the modern cloud and PoW period, uncertainty is intentionally wide because public anchors usually describe installed capacity, machine counts, or electricity use rather than realized functional bitops/s.

Landauer efficiency is computed as:

```text
eta_L = N_bitop k_B T ln(2) / P_wall
```

where `P_wall` is an associated system/wall-power denominator unless a narrower logic-power diagnostic is explicitly labeled.
