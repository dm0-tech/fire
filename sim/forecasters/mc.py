"""Monte Carlo forecaster. Draws its own shocks. Never receives the realised future."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from sim.model import PERP, draw_X, draw_eps, psi

_EPS = 1e-6


@dataclass
class Forecast:
    horizons: np.ndarray
    p_P: np.ndarray
    p_Q: np.ndarray
    theta: float
    phi_P: np.ndarray | None = None
    phi_Q: np.ndarray | None = None

    def at(self, maturity, measure: str = "Q") -> float:
        if maturity is None:
            target = int(self.horizons[0]) + 9
            idx = int(np.argmin(np.abs(self.horizons - target)))
        else:
            idx = int(np.argmin(np.abs(self.horizons - maturity)))
        series = self.p_Q if measure == "Q" else self.p_P
        return float(series[idx])


class MonteCarloForecaster:
    """Quantity-conditional physical expectation, then the multiplicative wedge.

    p^Q = p^P / (1 + θ), clipped into (ε, 1]. θ is the date's risk premium,
    not a horizon-specific price of risk.
    """

    name = "monte_carlo"
    n_paths = 48

    def forecast(self, state, book, policy, horizons, rng) -> Forecast:
        horizons = np.asarray(list(horizons), dtype=int)
        n_h = len(horizons)
        n = self.n_paths
        sov = state.sovereign
        S = np.full(n, state.S)
        lam = float(state.lam)
        crisis = np.full(n, state.in_crisis)
        phi = np.ones((n, n_h))
        probe = policy.q_probe
        x_m_share = float(policy.X_m_share)
        l_share = float(policy.L_share)
        previous_X_m = np.full(
            n, float(getattr(state, "current_X_m", x_m_share * sov.X_mean))
        )
        for i, maturity in enumerate(horizons):
            if sov.p_enter > 0 or state.in_crisis:
                stay = np.where(crisis, sov.p_stay, sov.p_enter)
                crisis = rng.random(n) < stay
            eps = draw_eps(
                rng, n, sov.sigma_eps, sov.jump_prob, sov.jump_size, crisis, sov.crisis_jump
            )
            g_previous = 1.0 - np.exp(-sov.kappa * previous_X_m)
            S = np.clip((1.0 - lam) * S + g_previous * (1.0 - S) + eps, 0.0, 1.0)
            X = draw_X(rng, n, sov.X_mean, sov.sigma_X)
            X_m = x_m_share * X
            L = l_share * X
            over = (X_m + L) > X
            scale = np.ones(n)
            scale[over] = X[over] / (X_m[over] + L[over])
            X_m = X_m * scale
            L = L * scale
            room = np.maximum(X - X_m - L, 0.0)
            Q = np.full(n, _quantity(book, int(maturity), probe))
            structural = np.array([psi(float(s), sov.S_min, sov.regime) for s in S])
            D = structural * np.minimum(Q, room)
            phi[:, i] = D / np.maximum(Q, _EPS)
            previous_X_m = X_m
        p_P = np.clip(phi.mean(axis=0), _EPS, 1.0)
        theta = max(0.0, float(state.theta))
        p_Q = np.clip(p_P / (1.0 + theta), _EPS, 1.0)
        secondary = getattr(state, "secondary_prices", {})
        market_weight = float(getattr(policy, "market_weight", 0.0))
        if secondary and market_weight > 0:
            observed = np.asarray([secondary.get(int(h), p_Q[i]) for i, h in enumerate(horizons)])
            p_Q = np.clip((1.0 - market_weight) * p_Q + market_weight * observed, _EPS, 1.0)
        phi_Q = np.column_stack([_map_to_mean(phi[:, i], p_Q[i]) for i in range(n_h)])
        return Forecast(horizons=horizons, p_P=p_P, p_Q=p_Q, theta=theta, phi_P=phi, phi_Q=phi_Q)


def _quantity(book, maturity: int, probe: float) -> float:
    q = book.quantity_at(maturity)
    return q if q > 0 else probe


def _map_to_mean(samples: np.ndarray, target: float) -> np.ndarray:
    """Push a fractional law toward zero or one to attain ``target`` exactly."""
    x = np.asarray(samples, dtype=float)
    target = float(np.clip(target, 0.0, 1.0))
    mean = float(x.mean())
    if target <= mean:
        return x * (target / mean) if mean > 0 else np.zeros_like(x)
    if mean >= 1.0:
        return np.full_like(x, target)
    return x + ((target - mean) / (1.0 - mean)) * (1.0 - x)
