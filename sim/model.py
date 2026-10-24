"""Physical economy. No I/O and no plotting.

Notation matches the symbol table in docs/MODEL.md. Probabilities are not
computed here; this module only realises delivery.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import math

import numpy as np

# Maturity sentinel: a perp pays `q` units of exergy every period.
PERP = None


def g(x: float, kappa: float) -> float:
    """Maintenance response. g(0) = 0, increasing, concave, g(∞) → 1."""
    return 1.0 - math.exp(-kappa * max(float(x), 0.0))


def psi(S: float, S_min: float, regime: str) -> float:
    """Structural delivery factor Ψ(S)."""
    if regime == "R1":
        if S_min <= 0:
            return 1.0
        return min(1.0, max(0.0, S / S_min))
    if regime == "R2":
        return 1.0 if S >= S_min else 0.0
    raise ValueError(f"unknown regime {regime}")


def deterministic_fixed_point(X_m: float, lam: float, kappa: float) -> float:
    """S* = g(X_m) / (λ + g(X_m)), with ε = 0 and constant maintenance."""
    gx = g(X_m, kappa)
    return gx / (lam + gx)


def step_S(S: float, X_m: float, lam: float, kappa: float, eps: float) -> float:
    nxt = (1.0 - lam) * S + g(X_m, kappa) * (1.0 - S) + eps
    return float(min(1.0, max(0.0, nxt)))


@dataclass
class Note:
    q: float
    maturity: int | None  # None marks a perp; q is then the per-period payment x


@dataclass
class NoteBook:
    notes: list[Note] = field(default_factory=list)

    def copy(self) -> "NoteBook":
        return NoteBook([Note(n.q, n.maturity) for n in self.notes if n.q > 0])

    def maturing_quantity(self, t: int) -> float:
        """Q_t, including the perp's current-period payment."""
        total = 0.0
        for n in self.notes:
            if n.maturity is None or n.maturity == t:
                total += n.q
        return total

    def money_stock(self, t: int, beta: float) -> float:
        """M_t = Σ q_i β^{t_i − t}. A perp contributes x β / (1 − β)."""
        if not 0.0 < beta < 1.0:
            raise ValueError("beta must lie in (0, 1)")
        total = 0.0
        for n in self.notes:
            if n.maturity is None:
                total += n.q * beta / (1.0 - beta)
            elif n.maturity >= t:
                total += n.q * (beta ** (n.maturity - t))
        return total

    def mint(self, q: float, maturity: int | None) -> None:
        if q < 0:
            raise ValueError("cannot mint a negative quantity")
        if q == 0:
            return
        for n in self.notes:
            if n.maturity == maturity:
                n.q += q
                return
        self.notes.append(Note(q, maturity))

    def retire_money(self, amount: float, t: int, beta: float) -> list[tuple[float, int | None]]:
        """Retire up to ``amount`` of money stock, shortest claims first.

        Returns the face quantities removed.  The engine separately accounts for
        the spot-exergy paid to acquire these claims; retirement is therefore not
        a costless deletion of liabilities.
        """
        remaining = max(0.0, float(amount))
        retired: list[tuple[float, int | None]] = []
        ordered = sorted(
            self.notes,
            key=lambda n: math.inf if n.maturity is None else max(0, n.maturity - t),
        )
        for note in ordered:
            if remaining <= 1e-12 or note.q <= 0:
                continue
            if note.maturity is None:
                weight = beta / (1.0 - beta)
            elif note.maturity >= t:
                weight = beta ** (note.maturity - t)
            else:
                continue
            face = min(note.q, remaining / weight)
            note.q -= face
            remaining -= face * weight
            retired.append((face, note.maturity))
        self.notes = [n for n in self.notes if n.q > 1e-12]
        return retired

    def extinguish_matured(self, t: int) -> None:
        """Dated notes maturing at t are extinguished whether or not fully honoured.

        The unhonoured fraction is a loss to the holder, not a rollover.
        Perps persist. See DECISIONS.md.
        """
        self.notes = [n for n in self.notes if n.maturity is None or n.maturity != t]

    def quantity_at(self, maturity: int) -> float:
        total = 0.0
        for n in self.notes:
            if n.maturity is None or n.maturity == maturity:
                total += n.q
        return total

    def dated_notes(self, t: int) -> list[tuple[float, int]]:
        """Outstanding dated notes with maturity >= t, as (q, maturity)."""
        return [(n.q, n.maturity) for n in self.notes if n.maturity is not None and n.maturity >= t]


def allocate(
    X: float,
    X_m: float,
    L: float,
    Q: float,
    S: float,
    S_min: float,
    regime: str,
    R: float = 0.0,
) -> dict:
    """Split the inflow. Delivery has priority over production, not over X_m or L.

    If X_m + L exceeds X, both are scaled down in proportion and delivery
    receives the residual. Recorded in DECISIONS.md.
    """
    X = float(X)
    X_m = max(0.0, float(X_m))
    L = max(0.0, float(L))
    Q = max(0.0, float(Q))
    R = max(0.0, float(R))
    if X_m + L > X and (X_m + L) > 0.0:
        scale = X / (X_m + L)
        X_m *= scale
        L *= scale
    room = X - X_m - L
    structural = psi(S, S_min, regime)
    deliverable = Q + R
    if deliverable <= 0.0:
        D_maturity = 0.0
        R_paid = 0.0
        phi = 1.0  # no promise outstanding; delivery is vacuous
    else:
        paid = structural * min(deliverable, max(room, 0.0))
        # Maturing claims and voluntary early redemptions share capacity
        # proportionally. Both are delivery against outstanding notes.
        ratio = paid / deliverable
        D_maturity = ratio * Q
        R_paid = ratio * R
        phi = ratio
    D = D_maturity + R_paid
    X_p = X - X_m - L - D
    if abs(X_p) < 1e-12:
        X_p = 0.0
    return {
        "X_p": X_p,
        "X_m": X_m,
        "D": D,
        "D_maturity": D_maturity,
        "R": R_paid,
        "R_requested": R,
        "L": L,
        "phi": phi,
        "Y": X_p * S,
        "Q": deliverable,
        "Q_maturity": Q,
        "structural": structural,
        "room": room,
    }


def draw_eps(
    rng: np.random.Generator,
    n: int,
    sigma: float,
    jump_prob: float,
    jump_size: float,
    crisis: np.ndarray | None = None,
    crisis_jump: float = 0.15,
) -> np.ndarray:
    """Mixture: small Gaussian plus a rare negative jump. Crisis adds a further jump."""
    eps = rng.normal(0.0, sigma, size=n)
    eps = eps - (rng.random(n) < jump_prob) * jump_size
    if crisis is not None:
        eps = eps - crisis.astype(float) * crisis_jump
    return eps


def draw_X(rng: np.random.Generator, n: int, X_mean: float, sigma_X: float) -> np.ndarray:
    """Lognormal inflow with mean X_mean."""
    if sigma_X == 0.0:
        return np.full(n, X_mean)
    return X_mean * np.exp(rng.normal(-0.5 * sigma_X**2, sigma_X, size=n))


@dataclass
class Sovereign:
    """Parameters (λ, κ, and the shock law) that characterise one issuer."""

    lam: float = 0.08
    kappa: float = 1.2
    S_min: float = 0.45
    regime: str = "R1"
    delta_lam: float = 0.05
    sigma_eps: float = 0.02
    jump_prob: float = 0.04
    jump_size: float = 0.20
    X_mean: float = 1.0
    sigma_X: float = 0.08
    # Two-state crisis, used when asking whether the yield curve can invert.
    # p_stay < 1 makes a crisis transient, so near-term delivery is worse than distant delivery.
    p_enter: float = 0.0
    p_stay: float = 0.35
    crisis_jump: float = 0.18
    name: str = "sovereign"


@dataclass
class Economy:
    sovereign: Sovereign = field(default_factory=Sovereign)
    delta: float = 0.03
    S: float = 0.75
    t: int = 0
    lam: float | None = None
    book: NoteBook = field(default_factory=NoteBook)
    in_crisis: bool = False

    def __post_init__(self) -> None:
        if self.lam is None:
            self.lam = self.sovereign.lam

    @property
    def beta(self) -> float:
        return math.exp(-self.delta)

    def step_crisis(self, rng: np.random.Generator) -> bool:
        p = self.sovereign.p_stay if self.in_crisis else self.sovereign.p_enter
        self.in_crisis = bool(rng.random() < p)
        return self.in_crisis


def step_theta(
    theta: float,
    S: float,
    rng: np.random.Generator,
    *,
    alpha: float = 0.75,
    theta_bar: float = 0.04,
    gamma: float = 1.2,
    sigma: float = 0.01,
    S_ref: float = 0.70,
) -> float:
    """Countercyclical risk premium. Spikes when S is below S_ref, then mean-reverts.

    Explicit process, not derived from a utility function. See DECISIONS.md.
    """
    shock = float(rng.normal(0.0, sigma))
    raw = (1.0 - alpha) * theta_bar + alpha * theta + gamma * max(0.0, S_ref - S) + shock
    return max(0.0, raw)
