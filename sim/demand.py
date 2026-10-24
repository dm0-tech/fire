"""Liquidity service, confidence index, price level, fixed-point bookkeeping.

No I/O. `p_Q` values passed in are pricing-measure delivery fractions.
"""

from __future__ import annotations

import math

from sim.model import NoteBook, PERP


def _sigmoid(z: float) -> float:
    if z >= 0:
        ez = math.exp(-z)
        return 1.0 / (1.0 + ez)
    ez = math.exp(z)
    return ez / (1.0 + ez)


def ell_threshold(p_bar: float, ell_bar: float, p_star: float, tau_ell: float) -> float:
    """ℓ(p̄) = ℓ̄ · σ((p̄ − p*) / τ). τ → 0 is a hard threshold."""
    if tau_ell <= 0:
        return ell_bar if p_bar >= p_star else 0.0
    return ell_bar * _sigmoid((p_bar - p_star) / tau_ell)


def ell_linear(p_bar: float, ell_bar: float) -> float:
    """Crude robustness check: ℓ(p̄) = ℓ̄ · p̄."""
    return ell_bar * max(0.0, min(1.0, p_bar))


def ell(p_bar: float, ell_bar: float, p_star: float, tau_ell: float, form: str) -> float:
    if form == "linear":
        return ell_linear(p_bar, ell_bar)
    if form == "threshold":
        return ell_threshold(p_bar, ell_bar, p_star, tau_ell)
    raise ValueError(form)


def confidence(book: NoteBook, t: int, beta: float, p_Q, probe_maturities=()) -> float:
    """Stock-weighted delivery confidence under Q.

    `p_Q` maps a maturity (or None for the perp) to p^Q.
    An empty book uses the quantity-conditional probe curve. This avoids a
    discontinuous jump from perfect confidence to the first issued note.
    """
    num = 0.0
    den = 0.0
    for n in book.notes:
        if n.q <= 0:
            continue
        if n.maturity is None:
            # Aggregate the forecast curve payment by payment, with the same
            # flat terminal-quote tail used by the budget functionals.
            horizon = 16
            for lag in range(1, horizon + 1):
                w = n.q * beta**lag
                num += w * float(p_Q(t + lag))
                den += w
            tail_w = n.q * beta ** (horizon + 1) / (1.0 - beta)
            num += tail_w * float(p_Q(t + horizon))
            den += tail_w
            continue
        elif n.maturity >= t:
            w = n.q * (beta ** (n.maturity - t))
            p = p_Q(n.maturity)
        else:
            continue
        num += w * float(p)
        den += w
    if den <= 0.0:
        probes = [float(p_Q(m)) for m in probe_maturities]
        return float(sum(probes) / len(probes)) if probes else 0.0
    return num / den


def price_level(M: float, ell_value: float, Y: float) -> float:
    """P = M / (ℓ Y). Infinite when real balances are zero."""
    denom = ell_value * Y
    if denom <= 0.0:
        return math.inf
    return M / denom


def find_sign_changes(scales, residuals) -> list[float]:
    """Issuance scales at which M(s) − M_target(s) changes sign.

    Every crossing is returned. The caller decides which basin to sit in.
    """
    scales = list(scales)
    residuals = list(residuals)
    roots: list[float] = []
    for i in range(len(scales) - 1):
        r0 = residuals[i]
        r1 = residuals[i + 1]
        if r0 == 0.0 or (r0 < 0.0 <= r1) or (r1 < 0.0 <= r0):
            if r0 == 0.0:
                roots.append(float(scales[i]))
            elif r0 != r1:
                w = abs(r0) / (abs(r0) + abs(r1))
                roots.append(float(scales[i] + w * (scales[i + 1] - scales[i])))
    if residuals and residuals[-1] == 0.0:
        last = float(scales[-1])
        if last not in roots:
            roots.append(last)
    return roots


def select_root(roots: list[float], previous: float) -> tuple[float | None, int]:
    """Closest root to the previous period's scale. Returns (scale, index)."""
    if not roots:
        return None, -1
    index = min(range(len(roots)), key=lambda i: abs(roots[i] - previous))
    return roots[index], index


def damped_fixed_point(
    evaluate,
    initial: float,
    lower: float,
    upper: float,
    *,
    damping: float = 0.5,
    tolerance: float = 1e-5,
    max_iter: int = 30,
) -> dict:
    """Solve ``residual(action)=0`` by damped secant updates.

    ``evaluate`` returns the signed stock residual. Bounds keep policy actions
    feasible. A caller may fall back to an all-root grid scan when this local
    basin does not converge.
    """
    x = min(upper, max(lower, float(initial)))
    prev_x = None
    prev_r = None
    for iteration in range(1, max_iter + 1):
        r = float(evaluate(x))
        if abs(r) <= tolerance:
            return {"value": x, "residual": r, "iterations": iteration, "converged": True}
        if prev_x is not None and prev_r is not None and abs(r - prev_r) > 1e-12:
            proposal = x - r * (x - prev_x) / (r - prev_r)
        else:
            proposal = x - r
        proposal = min(upper, max(lower, proposal))
        prev_x, prev_r = x, r
        x = x + damping * (proposal - x)
    r = float(evaluate(x))
    return {"value": x, "residual": r, "iterations": max_iter, "converged": abs(r) <= tolerance}
