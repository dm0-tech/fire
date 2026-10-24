"""Budget functionals, term structure, joint surprisal, mutual information.

No I/O. Surprisal is u = −log p, and the caller must say whether p is p^P or p^Q.
"""

from __future__ import annotations

import math

import numpy as np

_EPS = 1e-12


def surprisal(p: np.ndarray | float) -> np.ndarray | float:
    """u = −log p, with p clipped into (ε, 1]."""
    arr = np.asarray(p, dtype=float)
    out = -np.log(np.clip(arr, _EPS, 1.0))
    if np.ndim(p) == 0:
        return float(out)
    return out


def hazard(u: np.ndarray) -> np.ndarray:
    """Forward hazard h(t) = u(t+1) − u(t)."""
    u = np.asarray(u, dtype=float)
    return np.diff(u)


def yield_curve(u: np.ndarray, delta: float, maturities: np.ndarray) -> np.ndarray:
    """r(t) = δ + u(t) / (t − s). `maturities` is (t − s), strictly positive."""
    m = np.asarray(maturities, dtype=float)
    if np.any(m <= 0):
        raise ValueError("maturity must be strictly positive")
    return delta + np.asarray(u, dtype=float) / m


def aggregate(q, values, beta: float | None = None, maturities=None) -> float:
    """Σ q_i v_i, or Σ q_i v_i β^{m_i} when a discount factor is supplied."""
    q = np.asarray(q, dtype=float)
    v = np.asarray(values, dtype=float)
    if beta is None:
        return float(np.sum(q * v))
    m = np.asarray(maturities, dtype=float)
    return float(np.sum(q * v * (beta ** m)))


def U0(q, u) -> float:
    return aggregate(q, u)


def U1(q, u, beta: float, maturities) -> float:
    return aggregate(q, u, beta, maturities)


def U2(q, p, beta: float, maturities) -> float:
    shortfall = 1.0 - np.asarray(p, dtype=float)
    return aggregate(q, shortfall, beta, maturities)


def U3(q, u, beta: float, maturities) -> float:
    """Mean surprisal per promised unit. Dimensionless (nats)."""
    q = np.asarray(q, dtype=float)
    u = np.asarray(u, dtype=float)
    m = np.asarray(maturities, dtype=float)
    w = q * (beta ** m)
    den = float(np.sum(w))
    if den <= 0.0:
        return 0.0
    return float(np.sum(w * u) / den)


def book_functionals(book_rows: list[tuple[float, int]], p_of, t: int, beta: float, rule: str) -> float:
    """Aggregate a dated book. `p_of(maturity)` returns the priced or physical delivery fraction.

    Perp rows use maturity None and are expanded by the caller via `perp_rows`.
    """
    if not book_rows:
        return 0.0
    q = []
    p = []
    m = []
    for qty, maturity in book_rows:
        lag = maturity - t
        if lag < 0 or qty <= 0:
            continue
        q.append(qty)
        p.append(p_of(maturity))
        m.append(lag)
    if not q:
        return 0.0
    q = np.asarray(q)
    p = np.clip(np.asarray(p, dtype=float), _EPS, 1.0)
    u = -np.log(p)
    m = np.asarray(m, dtype=float)
    if rule == "B0":
        return U0(q, u)
    if rule == "B1":
        return U1(q, u, beta, m)
    if rule == "B2":
        return U2(q, p, beta, m)
    if rule == "B3":
        return U3(q, u, beta, m)
    raise ValueError(rule)


def book_functional_with_perps(
    dated_rows: list[tuple[float, int]],
    perp_payments: list[float],
    p_of,
    t: int,
    beta: float,
    rule: str,
    *,
    tail_horizon: int = 16,
) -> float:
    """Book functional with an infinite, flat-forecast perp tail.

    The forecaster is defined on a finite horizon and extrapolates its terminal
    quote. Under that explicit flat-tail convention B1--B3 have exact geometric
    tails. B0 is infinite for every perp with positive terminal surprisal and is
    therefore infeasible, rather than silently truncated.
    """
    rows = list(dated_rows)
    for x in perp_payments:
        rows.extend((x, t + lag) for lag in range(1, tail_horizon + 1))
    if not perp_payments:
        return book_functionals(rows, p_of, t, beta, rule)
    terminal_p = float(np.clip(p_of(t + tail_horizon), _EPS, 1.0))
    terminal_u = -math.log(terminal_p)
    if rule == "B0" and terminal_u > 0.0:
        return math.inf
    q = np.asarray([q for q, _ in rows], dtype=float)
    m = np.asarray([maturity - t for _, maturity in rows], dtype=float)
    p = np.asarray([p_of(maturity) for _, maturity in rows], dtype=float)
    u = -np.log(np.clip(p, _EPS, 1.0))
    tail_weight = sum(perp_payments) * beta ** (tail_horizon + 1) / (1.0 - beta)
    if rule == "B0":
        return float(np.sum(q * u))
    if rule == "B1":
        return float(np.sum(q * u * beta**m) + tail_weight * terminal_u)
    if rule == "B2":
        return float(np.sum(q * (1.0 - p) * beta**m) + tail_weight * (1.0 - terminal_p))
    if rule == "B3":
        numerator = float(np.sum(q * u * beta**m) + tail_weight * terminal_u)
        denominator = float(np.sum(q * beta**m) + tail_weight)
        return numerator / denominator if denominator > 0 else 0.0
    raise ValueError(rule)


def perp_partial(x: float, h: float, beta: float, H: int) -> dict[str, np.ndarray]:
    """Partial sums of a perp under constant hazard h, for horizons 1..H.

    u(m) = h m. B0 is the running sum of x u(m). B1 and B2 are discounted running sums.
    B3 is the discounted-mean surprisal of the truncated perp.
    """
    m = np.arange(1, H + 1, dtype=float)
    u = h * m
    p = np.exp(-u)
    w = x * (beta ** m)
    b0 = np.cumsum(x * u)
    b1 = np.cumsum(x * u * (beta ** m))
    b2 = np.cumsum(x * (1.0 - p) * (beta ** m))
    b3 = np.cumsum(w * u) / np.cumsum(w)
    return {"B0": b0, "B1": b1, "B2": b2, "B3": b3, "m": m}


def closed_form_perp_B1(x: float, h: float, beta: float) -> float:
    """Σ_{m=1}^∞ x (h m) β^m = x h β / (1 − β)^2."""
    return x * h * beta / (1.0 - beta) ** 2


def joint_surprisal(phi_paths: np.ndarray, eta: float) -> tuple[float, float]:
    """U^joint = −log P(φ_τ ≥ 1 − η for every horizon).

    `phi_paths` has shape (n_paths, n_horizons). Returns (surprisal, probability).
    """
    if phi_paths.size == 0:
        return 0.0, 1.0
    ok = np.all(phi_paths >= (1.0 - eta), axis=1)
    prob = float(np.mean(ok))
    prob = max(prob, _EPS)
    return -math.log(prob), prob


def positive_dependence_gap(phi_paths: np.ndarray, eta: float) -> float:
    """log P(all) − Σ log P(one). Positive when delivery events are positively dependent.

    The inequality U^joint ≤ Σ u_i is this gap being non-negative, and it reverses
    under negative dependence. It is a property of the shock structure, not an identity.
    """
    success = phi_paths >= (1.0 - eta)
    if success.shape[1] == 0:
        return 0.0
    joint = max(float(np.mean(np.all(success, axis=1))), _EPS)
    marginals = np.clip(success.mean(axis=0), _EPS, 1.0)
    return math.log(joint) - float(np.sum(np.log(marginals)))


def binary_mutual_information(a: np.ndarray, b: np.ndarray) -> float:
    """I(A; B) in nats for two boolean arrays. A scalar summary, not a price."""
    a = np.asarray(a, dtype=bool)
    b = np.asarray(b, dtype=bool)
    n = len(a)
    if n == 0:
        return 0.0
    counts = {
        (True, True): np.sum(a & b),
        (True, False): np.sum(a & ~b),
        (False, True): np.sum(~a & b),
        (False, False): np.sum(~a & ~b),
    }

    def entropy(ps: list[float]) -> float:
        h = 0.0
        for p in ps:
            if p > 0.0:
                h -= p * math.log(p)
        return h

    joint_ps = [c / n for c in counts.values()]
    pa = float(np.mean(a))
    pb = float(np.mean(b))
    return entropy([pa, 1.0 - pa]) + entropy([pb, 1.0 - pb]) - entropy(joint_ps)


def bernoulli_kl(p: float, q: float) -> float:
    """D(Bern(p) ‖ Bern(q)) in nats. The fractional-φ stand-in recorded in DECISIONS.md."""
    p = float(np.clip(p, _EPS, 1.0 - _EPS))
    q = float(np.clip(q, _EPS, 1.0 - _EPS))
    return p * math.log(p / q) + (1.0 - p) * math.log((1.0 - p) / (1.0 - q))


def empirical_kl(p_samples, q_samples, bins: int = 10, smoothing: float = 0.5) -> float:
    """Histogram estimate of KL for fractional delivery laws on [0, 1]."""
    p_samples = np.clip(np.asarray(p_samples, dtype=float).ravel(), 0.0, 1.0)
    q_samples = np.clip(np.asarray(q_samples, dtype=float).ravel(), 0.0, 1.0)
    if p_samples.size == 0 or q_samples.size == 0:
        return 0.0
    edges = np.linspace(0.0, 1.0, bins + 1)
    pc = np.histogram(p_samples, bins=edges)[0].astype(float) + smoothing
    qc = np.histogram(q_samples, bins=edges)[0].astype(float) + smoothing
    pp = pc / pc.sum()
    qp = qc / qc.sum()
    return float(np.sum(pp * np.log(pp / qp)))


def mean_horizon_kl(p_paths, q_paths, bins: int = 10, smoothing: float = 0.5) -> float:
    """Mean of horizon-specific fractional-law divergences."""
    p_paths = np.asarray(p_paths, dtype=float)
    q_paths = np.asarray(q_paths, dtype=float)
    if p_paths.shape != q_paths.shape or p_paths.ndim != 2:
        raise ValueError("delivery paths must be equally shaped 2D arrays")
    if p_paths.shape[1] == 0:
        return 0.0
    return float(
        np.mean(
            [
                empirical_kl(p_paths[:, i], q_paths[:, i], bins, smoothing)
                for i in range(p_paths.shape[1])
            ]
        )
    )
