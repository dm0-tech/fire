"""Coupled two-issuer delivery simulation and bridge capacity accounting."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from sim.measures import binary_mutual_information
from sim.model import Sovereign, allocate, step_S


@dataclass(frozen=True)
class BridgeClaim:
    q: float
    maturity: int


def coupled_bridge(
    common_share: float,
    *,
    n_paths: int = 512,
    horizon: int = 5,
    seed: int = 0,
    ceiling: float = 0.8,
    beta: float = float(np.exp(-0.03)),
) -> dict:
    """Run two issuers on common/idiosyncratic shocks and price a bridge.

    The bridge delivers only to the extent both issuers deliver. Capacity is the
    maximum bridge face value admitted by B1 at the estimated joint quote.
    """
    rng = np.random.default_rng(seed)
    share = float(np.clip(common_share, 0.0, 1.0))
    sov_j = Sovereign(name="j", regime="R2")
    sov_k = Sovereign(name="k", regime="R2", lam=0.10, kappa=1.1)
    S_j = np.full(n_paths, 0.75)
    S_k = np.full(n_paths, 0.75)
    phi_j = np.ones((n_paths, horizon))
    phi_k = np.ones((n_paths, horizon))
    for h in range(horizon):
        common = rng.normal(0.0, 0.05, n_paths) - (rng.random(n_paths) < 0.12) * 0.30
        idio_j = rng.normal(0.0, 0.05, n_paths)
        idio_k = rng.normal(0.0, 0.05, n_paths)
        eps_j = np.sqrt(share) * common + np.sqrt(1.0 - share) * idio_j
        eps_k = np.sqrt(share) * common + np.sqrt(1.0 - share) * idio_k
        X_j = sov_j.X_mean * np.exp(rng.normal(-0.5 * sov_j.sigma_X**2, sov_j.sigma_X, n_paths))
        X_k = sov_k.X_mean * np.exp(rng.normal(-0.5 * sov_k.sigma_X**2, sov_k.sigma_X, n_paths))
        for i in range(n_paths):
            out_j = allocate(X_j[i], 0.2 * X_j[i], 0.0, 0.3, S_j[i], sov_j.S_min, sov_j.regime)
            out_k = allocate(X_k[i], 0.2 * X_k[i], 0.0, 0.3, S_k[i], sov_k.S_min, sov_k.regime)
            phi_j[i, h] = out_j["phi"]
            phi_k[i, h] = out_k["phi"]
            S_j[i] = step_S(S_j[i], out_j["X_m"], sov_j.lam, sov_j.kappa, eps_j[i])
            S_k[i] = step_S(S_k[i], out_k["X_m"], sov_k.lam, sov_k.kappa, eps_k[i])
    j = phi_j[:, -1]
    k = phi_k[:, -1]
    bridge_delivery = np.minimum(j, k)
    p_j = float(j.mean())
    p_k = float(k.mean())
    joint_price = max(float(bridge_delivery.mean()), 1e-12)
    marginal_price = max(p_j * p_k, 1e-12)
    u_joint = -np.log(joint_price)
    u_marginal = -np.log(marginal_price)
    discount = beta**horizon
    # A near-certain bridge has a very large but finite reported capacity so
    # summaries remain strict JSON. The floor is a numerical reporting bound.
    joint_capacity = ceiling / (max(u_joint, 1e-12) * discount)
    marginal_capacity = ceiling / (max(u_marginal, 1e-12) * discount)
    success_j = j >= 0.95
    success_k = k >= 0.95
    return {
        "share": share,
        "horizon": horizon,
        "p_j": p_j,
        "p_k": p_k,
        "marginal_price": marginal_price,
        "joint_price": joint_price,
        "price_gap": marginal_price - joint_price,
        "mutual_information": binary_mutual_information(success_j, success_k),
        "joint_capacity": joint_capacity,
        "marginal_capacity": marginal_capacity,
        "capacity_gap": joint_capacity - marginal_capacity,
        "claim": BridgeClaim(q=joint_capacity, maturity=horizon),
        "phi_j": phi_j,
        "phi_k": phi_k,
    }
