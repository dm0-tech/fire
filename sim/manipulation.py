"""LMSR delivery market and the exergy levy that funds it.

Costs are in exergy. The endowment holds exergy, never the issuer's notes.
"""

from __future__ import annotations

import math


class LMSR:
    """Logarithmic market scoring rule for a two-outcome delivery contract.

    Price of YES is the pricing-measure quote the attacker is trying to move.
    """

    def __init__(self, b: float, p0: float):
        if b <= 0:
            raise ValueError("LMSR liquidity must be positive")
        p0 = min(1.0 - 1e-6, max(1e-6, p0))
        self.b = float(b)
        self.q_yes = self.b * math.log(p0 / (1.0 - p0))
        self.q_no = 0.0

    def price(self) -> float:
        ey = math.exp(self.q_yes / self.b)
        en = math.exp(self.q_no / self.b)
        return ey / (ey + en)

    def cost(self) -> float:
        return self.b * math.log(math.exp(self.q_yes / self.b) + math.exp(self.q_no / self.b))

    def _spend(self, side: str, budget: float) -> float:
        """Buy `side` until `budget` of exergy is spent, or the price saturates."""
        if budget <= 0:
            return 0.0
        start = self.cost()
        target = start + budget
        lo, hi = 0.0, budget + self.b * 10.0
        for _ in range(60):
            mid = 0.5 * (lo + hi)
            if side == "yes":
                self.q_yes += mid
            else:
                self.q_no += mid
            spent = self.cost() - start
            if side == "yes":
                self.q_yes -= mid
            else:
                self.q_no -= mid
            if spent < budget:
                lo = mid
            else:
                hi = mid
        move = lo
        if side == "yes":
            self.q_yes += move
        else:
            self.q_no += move
        return self.cost() - start

    def buy_yes(self, budget: float) -> float:
        return self._spend("yes", budget)

    def buy_no(self, budget: float) -> float:
        return self._spend("no", budget)


def levy(q_and_p_and_lag: list[tuple[float, float, int]], zeta: float, beta: float) -> float:
    """L = ζ Σ q_i p^Q(t_i) β^{t_i − t} over notes minted this period."""
    total = 0.0
    for q, p, lag in q_and_p_and_lag:
        total += q * p * (beta ** lag)
    return zeta * total


def liquidity_parameter(W: float, b_scale: float = 1.0, W_floor: float = 0.02) -> float:
    """b ∝ endowment. A floor keeps an empty endowment thin rather than undefined."""
    return b_scale * max(W, W_floor)


def manipulate(
    p_fair: float,
    attacker_budget: float,
    endowment: float,
    *,
    b_scale: float = 1.0,
    W_floor: float = 0.02,
) -> dict:
    """Attacker buys YES, then the endowment buys NO back toward p_fair.

    The endowment spends at most its exergy balance, and only while the price
    sits above its own fair-value estimate. Returns the prices and the exergy spent.
    """
    b = liquidity_parameter(endowment, b_scale, W_floor)
    market = LMSR(b, p_fair)
    spent_attack = market.buy_yes(attacker_budget)
    p_after_attack = market.price()
    defend_budget = 0.0
    if market.price() > p_fair and endowment > 0:
        # Spend only what is needed to walk the price back, capped by W.
        defend_budget = min(endowment, attacker_budget + endowment)
        market.buy_no(defend_budget)
        # If we overshot below fair value, that is the endowment overpaying.
        # Clip the recorded defence at the point price crossed p_fair by
        # re-running with a binary search when the full budget overshoots.
        if market.price() < p_fair:
            market = LMSR(b, p_fair)
            market.buy_yes(attacker_budget)
            lo, hi = 0.0, defend_budget
            for _ in range(40):
                mid = 0.5 * (lo + hi)
                trial = LMSR(b, p_fair)
                trial.buy_yes(attacker_budget)
                trial.buy_no(mid)
                if trial.price() > p_fair:
                    lo = mid
                else:
                    hi = mid
            market = LMSR(b, p_fair)
            market.buy_yes(attacker_budget)
            market.buy_no(hi)
            defend_budget = hi
    return {
        "p_fair": p_fair,
        "p_after_attack": p_after_attack,
        "p_final": market.price(),
        "bias": market.price() - p_fair,
        "spent_attack": spent_attack,
        "spent_defence": defend_budget,
        "b": b,
        "W": endowment,
    }
