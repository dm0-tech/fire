"""Mean-field forecaster. Propagates E[S] and a horizon variance penalty.

A different estimator from the Monte Carlo forecaster, so the two can be scored
against the same realised deliveries. It does not read future shocks.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from sim.model import psi

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


class MeanFieldForecaster:
    name = "mean_field"

    def forecast(self, state, book, policy, horizons, rng) -> Forecast:
        # `rng` is accepted so the signature matches the Monte Carlo forecaster.
        # This estimator does not draw shocks. Touching the generator would
        # spend randomness the caller might have wanted left alone, so it is unused.
        del rng
        horizons = np.asarray(list(horizons), dtype=int)
        sov = state.sovereign
        S = float(state.S)
        lam = float(state.lam)
        p_crisis = 1.0 if state.in_crisis else 0.0
        p_P = []
        x_m_share = float(policy.X_m_share)
        l_share = min(0.9, float(policy.L_share))
        previous_X_m = float(getattr(state, "current_X_m", x_m_share * sov.X_mean))
        X = sov.X_mean
        var = 0.0
        for maturity in horizons:
            if sov.p_enter > 0 or state.in_crisis:
                p_crisis = p_crisis * sov.p_stay + (1.0 - p_crisis) * sov.p_enter
            g_previous = 1.0 - np.exp(-sov.kappa * previous_X_m)
            S = float(np.clip((1.0 - lam) * S + g_previous * (1.0 - S), 0.0, 1.0))
            X_m = x_m_share * X
            L = l_share * X
            if X_m + L > X:
                scale = X / (X_m + L)
                X_m *= scale
                L *= scale
            room = max(X - X_m - L, 0.0)
            q = book.quantity_at(int(maturity))
            Q = q if q > 0 else policy.q_probe
            structural = psi(S, sov.S_min, sov.regime)
            # Capacity shortfall on the mean path, then a penalty for accumulated variance
            # and for the probability of still being in crisis.
            mean_phi = structural * min(1.0, room / Q) if Q > 0 else 1.0
            var = var + sov.sigma_eps**2 + sov.jump_prob * sov.jump_size**2
            damp = np.exp(-0.5 * var) * (1.0 - 0.5 * p_crisis * sov.crisis_jump)
            p_P.append(float(np.clip(mean_phi * damp, _EPS, 1.0)))
            previous_X_m = X_m
        p_P = np.asarray(p_P)
        theta = max(0.0, float(state.theta))
        p_Q = np.clip(p_P / (1.0 + theta), _EPS, 1.0)
        secondary = getattr(state, "secondary_prices", {})
        market_weight = float(getattr(policy, "market_weight", 0.0))
        if secondary and market_weight > 0:
            observed = np.asarray([secondary.get(int(h), p_Q[i]) for i, h in enumerate(horizons)])
            p_Q = np.clip((1.0 - market_weight) * p_Q + market_weight * observed, _EPS, 1.0)
        return Forecast(
            horizons=horizons,
            p_P=p_P,
            p_Q=p_Q,
            theta=theta,
            phi_P=p_P[None, :],
            phi_Q=p_Q[None, :],
        )
