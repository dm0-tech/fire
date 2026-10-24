"""Maintenance and issuance modes.

The engine turns a mode into quantities. Policies do not read future shocks.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Obs:
    t: int
    S: float
    X: float
    ceiling_bound_last: bool
    base_share: float = 0.25


def maintenance_share(mode: str, obs: Obs) -> float:
    """Fraction of this period's inflow devoted to maintenance before the levy.

    `greedy` is the issuance-maximising corner: almost all exergy goes to
    structure. `budget_seeking` raises maintenance only after the ceiling bound.
    """
    if mode == "constant":
        return obs.base_share
    if mode == "greedy":
        return 0.85
    if mode == "budget_seeking":
        if obs.ceiling_bound_last:
            return min(0.80, obs.base_share + 0.20)
        return max(0.05, obs.base_share - 0.05)
    raise ValueError(mode)


# Ladders tried from longest to shortest. B3 rejects a long ladder once mean
# surprisal exceeds ū; the issuer then shortens rather than minting nothing.
LADDERS: tuple[tuple[int, ...], ...] = (
    (1, 2, 4, 8, 16),
    (1, 2, 4),
    (1, 2),
    (1,),
)


def ladder_allocations(lags: tuple[int, ...], total_face: float) -> list[tuple[float, int]]:
    """Split a total issuance quantity equally across the selected rungs."""
    if not lags or total_face <= 0:
        return []
    per_rung = float(total_face) / len(lags)
    return [(per_rung, lag) for lag in lags]


@dataclass
class PolicyConfig:
    name: str
    maintenance: str = "constant"
    issuance: str = "price_target"  # or "fill_ceiling"
    repair: bool = False
    base_share: float = 0.25
    rule: str = "B3"
    B_bar_0: float = 0.40
    rho: float = 0.0
    k: int = 2
    zeta: float = 0.0
    ell_form: str = "threshold"
    reflexive: bool = False
    reflexive_drop: float = 0.45
    reflexive_at: int = 15
    market_weight: float = 0.0
    exit_haircut: float = 0.45
    allow_retirement: bool = True
    perp_payment: float = 0.0
    attack_budget_ratio: float = 0.0


def v1_brake() -> PolicyConfig:
    """Pure surprisal ceiling. No demand channel, no repair."""
    return PolicyConfig(
        name="v1_brake",
        maintenance="constant",
        issuance="fill_ceiling",
        repair=False,
        rho=0.0,
        rule="B1",
        B_bar_0=0.80,
    )


def price_target() -> PolicyConfig:
    return PolicyConfig(
        name="price_target",
        maintenance="constant",
        issuance="price_target",
        repair=False,
        rho=0.0,
        rule="B3",
    )


def price_target_repair() -> PolicyConfig:
    return PolicyConfig(
        name="price_target_repair",
        maintenance="constant",
        issuance="price_target",
        repair=True,
        rho=0.8,
        rule="B3",
    )
