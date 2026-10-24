"""Selected forecaster.

`choose()` scores the two estimators on realised delivery and re-exports the winner.
Experiments import `Forecaster` from here and do not switch it afterwards.
"""

from __future__ import annotations

import numpy as np

from sim.forecasters.mc import Forecast, MonteCarloForecaster
from sim.forecasters.meanfield import MeanFieldForecaster
from sim.model import Economy, NoteBook, Sovereign

# Placeholder until choose() runs. Monte Carlo is the default if selection is skipped.
Forecaster = MonteCarloForecaster
SELECTED_NAME = MonteCarloForecaster.name


class _PolicyView:
    def __init__(self, X_m_share: float, L_share: float, q_probe: float):
        self.X_m_share = X_m_share
        self.L_share = L_share
        self.q_probe = q_probe


def brier_score(forecaster, n_origins: int = 24, horizon: int = 8, seed: int = 7) -> float:
    """Mean squared error of p^P against realised φ. The forecaster never sees those shocks."""
    rng = np.random.default_rng(seed)
    errors = []
    for _ in range(n_origins):
        sov = Sovereign()
        S0 = float(rng.uniform(0.4, 0.9))
        state = Economy(sovereign=sov, S=S0, lam=sov.lam)
        state.theta = 0.04
        book = NoteBook()
        book.mint(0.2, state.t + 3)
        policy = _PolicyView(0.25, 0.0, 0.05 * sov.X_mean)
        horizons = [state.t + h for h in range(1, horizon + 1)]
        # Separate stream from the one that will realise the path.
        forecast_rng = np.random.default_rng(rng.integers(1, 2**31 - 1))
        cast = forecaster.forecast(state, book, policy, horizons, forecast_rng)
        realised = _realise(state, book, policy, horizons, rng)
        errors.append((cast.p_P - realised) ** 2)
    return float(np.mean(errors))


def _realise(state, book, policy, horizons, rng) -> np.ndarray:
    """One physical path. This is the outcome the score is computed against."""
    from sim.model import allocate, draw_X, draw_eps, step_S

    S = state.S
    phi = []
    for maturity in horizons:
        X = float(draw_X(rng, 1, state.sovereign.X_mean, state.sovereign.sigma_X)[0])
        eps = float(draw_eps(rng, 1, state.sovereign.sigma_eps, state.sovereign.jump_prob, state.sovereign.jump_size)[0])
        X_m = policy.X_m_share * X
        Q = book.quantity_at(int(maturity)) or policy.q_probe
        L = policy.L_share * X
        S = step_S(S, X_m, state.lam, state.sovereign.kappa, eps)
        out = allocate(
            X, X_m, L, Q, S, state.sovereign.S_min, state.sovereign.regime
        )
        phi.append(out["phi"])
    return np.asarray(phi)


def choose(seed: int = 7) -> str:
    """Pick the forecaster with the lower Brier score. Does not blend them."""
    global Forecaster, SELECTED_NAME
    candidates = [MonteCarloForecaster(), MeanFieldForecaster()]
    scores = {c.name: brier_score(c, seed=seed) for c in candidates}
    winner = min(scores, key=scores.get)
    Forecaster = MonteCarloForecaster if winner == MonteCarloForecaster.name else MeanFieldForecaster
    SELECTED_NAME = winner
    choose.scores = scores  # type: ignore[attr-defined]
    return winner
