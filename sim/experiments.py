"""Experiment calculations. Figures are written by the runners, not here.

Each function reports what happened. It does not decide whether that matched a prediction.
"""

from __future__ import annotations

from dataclasses import replace

import numpy as np

from sim.bridge import coupled_bridge
from sim.engine import run
from sim.manipulation import manipulate
from sim.measures import (
    binary_mutual_information,
    closed_form_perp_B1,
    perp_partial,
    surprisal,
)
from sim.model import Economy, NoteBook, Sovereign, draw_eps, psi, step_S
from sim.policies import PolicyConfig, price_target, price_target_repair, v1_brake


def _forecaster(n_paths: int = 128):
    from sim.forecaster import Forecaster

    caster = Forecaster()
    if hasattr(caster, "n_paths"):
        caster.n_paths = n_paths
    return caster


def _interval(values) -> dict:
    values = np.asarray(values, dtype=float)
    return {
        "median": float(np.nanmedian(values)),
        "q10": float(np.nanquantile(values, 0.10)),
        "q90": float(np.nanquantile(values, 0.90)),
    }


def _paths(T: int, seed: int, sovereign: Sovereign):
    rng = np.random.default_rng(seed)
    X = sovereign.X_mean * np.exp(rng.normal(-0.5 * sovereign.sigma_X**2, sovereign.sigma_X, size=T))
    eps = draw_eps(rng, T, sovereign.sigma_eps, sovereign.jump_prob, sovereign.jump_size)
    return X, eps


def e4_volatility(sigma: float = 0.2, T: int = 200, n: int = 400, seed: int = 0) -> dict:
    """Martingale noise in p, physical state held fixed. One note, so each functional is a scalar multiple of u or of (1-p)."""
    rng = np.random.default_rng(seed)
    du = np.empty((n, T - 1))
    d_short = np.empty((n, T - 1))
    for i in range(n):
        p = 0.65
        u_prev = -np.log(p)
        s_prev = 1.0 - p
        for t in range(T - 1):
            p = float(np.clip(p * np.exp(-0.5 * sigma**2 + sigma * rng.normal()), 1e-6, 1 - 1e-6))
            u = -np.log(p)
            du[i, t] = u - u_prev
            d_short[i, t] = (1.0 - p) - s_prev
            u_prev, s_prev = u, 1.0 - p
    return {
        "sigma2_over_2": 0.5 * sigma**2,
        "mean_du": float(du.mean()),
        "mean_d_shortfall": float(d_short.mean()),
        "du_path": du.mean(axis=0),
        "short_path": d_short.mean(axis=0),
    }


def e8_perp(h: float = 0.05, beta: float = 0.96, H: int = 300) -> dict:
    parts = perp_partial(1.0, h, beta, H)
    closed = closed_form_perp_B1(1.0, h, beta)
    return {
        "m": parts["m"],
        "B0": parts["B0"],
        "B1": parts["B1"],
        "B2": parts["B2"],
        "B3": parts["B3"],
        "B1_closed": closed,
        "B0_still_rising": bool(parts["B0"][-1] > parts["B0"][H // 2] * 1.5),
        "B1_gap": float(abs(parts["B1"][-1] - closed) / closed),
    }


def e8_growth(T: int = 30, seed: int = 4) -> dict:
    caster = _forecaster()
    cfg = replace(price_target(), perp_payment=0.01)
    result = run(cfg, T=T, seed=seed, forecaster=caster, n_grid=7)
    M = result.series("M")
    Y = result.series("Y")
    kl = result.series("kl")
    # Growth rates use the first strictly positive observation as the base.
    def rate(series):
        positive = np.where(series > 1e-8)[0]
        if len(positive) < 2:
            return 0.0
        a, b = positive[0], positive[-1]
        return float(np.log(series[b] / series[a]) / (b - a))

    g_M = rate(M)
    g_Y = rate(Y)
    mean_kl = float(np.mean(kl))
    return {
        "g_M": g_M,
        "g_Y": g_Y,
        "mean_kl": mean_kl,
        "excess": g_M - g_Y,
        "within_bound": bool(g_M - g_Y <= mean_kl + 1e-6),
        "M": M,
        "Y": Y,
        "kl": kl,
    }


def _yields(record, delta: float) -> np.ndarray:
    u = np.asarray(record["u"], dtype=float)
    lags = np.asarray(record["horizons"], dtype=float) - record["t"]
    return delta + u / np.maximum(lags, 1.0)


def e1_sovereigns(T: int = 24, seed: int = 2) -> dict:
    healthy = Sovereign(lam=0.04, name="healthy")
    weak = Sovereign(lam=0.20, name="weak")
    X, eps = _paths(T, seed, healthy)
    caster = _forecaster()
    out = {}
    for sov in (healthy, weak):
        result = run(
            price_target(),
            T=T,
            seed=seed,
            sovereign=sov,
            forecaster=caster,
            X_path=X,
            eps_path=eps,
            n_grid=7,
        )
        snaps = {}
        for t in (0, T // 2, T - 1):
            snaps[t] = {
                "lags": (np.asarray(result.records[t]["horizons"]) - t).tolist(),
                "r": _yields(result.records[t], 0.03).tolist(),
                "u": result.records[t]["u"],
            }
        slopes = {}
        for t, snap in snaps.items():
            r = np.asarray(snap["r"], dtype=float)
            slopes[t] = float(r[-1] - r[0])
        out[sov.name] = {
            "S": result.series("S"),
            "Y": result.series("Y"),
            "U": result.series("U"),
            "snaps": snaps,
            "yield_slope": slopes,
        }
    # Inversion probe: start in a transient crisis.
    economy_style = Sovereign(lam=0.08, p_enter=0.0, p_stay=0.3, crisis_jump=0.25)
    # Forecast directly from a crisis state so the curve is conditional on being in crisis now.
    state = Economy(sovereign=economy_style, S=0.7, lam=economy_style.lam)
    state.in_crisis = True
    state.theta = 0.04
    state.reflexive_factor = 1.0
    book = NoteBook()

    class _P:
        X_m_share = 0.25
        L_share = 0.0
        q_probe = 0.05

    horizons = list(range(1, 13))
    cast = caster.forecast(state, book, _P(), horizons, np.random.default_rng(0))
    u = surprisal(cast.p_Q)
    r = 0.03 + u / np.arange(1, 13)
    hazard = np.diff(u)
    out["crisis_curve"] = {
        "r": r.tolist(),
        "hazard": hazard.tolist(),
        "falling_hazard": bool(hazard[0] > hazard[-1]),
        "inverted_yield": bool(r[0] > r[-1]),
    }
    out["X"] = X
    return out


def e2_overissue(T: int = 24, seed: int = 5) -> dict:
    sov = Sovereign(lam=0.06)
    X, eps = _paths(T, seed, sov)
    caster = _forecaster()
    aggressive = PolicyConfig(
        name="overissue",
        maintenance="constant",
        issuance="fill_ceiling",
        base_share=0.02,
        rule="B1",
        B_bar_0=0.35,
    )
    calm = replace(aggressive, name="calm", issuance="price_target", base_share=0.25, rule="B3", B_bar_0=0.40)
    aggressive_run = run(aggressive, T=T, seed=seed, sovereign=sov, forecaster=caster, X_path=X, eps_path=eps, n_grid=7)
    calm_run = run(calm, T=T, seed=seed, sovereign=sov, forecaster=caster, X_path=X, eps_path=eps, n_grid=7)
    binds = np.where(aggressive_run.series("ceiling_binds") > 0.5)[0]
    first_bind = int(binds[0]) if len(binds) else None
    S = aggressive_run.series("S")
    return {
        "aggressive_S": S,
        "aggressive_U": aggressive_run.series("U"),
        "aggressive_B": aggressive_run.series("B_bar"),
        "aggressive_r0": [_yields(row, 0.03)[0] for row in aggressive_run.records],
        "calm_S": calm_run.series("S"),
        "first_bind": first_bind,
        "S_at_bind": None if first_bind is None else float(S[first_bind]),
        "S_min_after": None if first_bind is None else float(S[first_bind:].min()),
    }


def e5_premium(thetas: np.ndarray | None = None) -> dict:
    """Physical delivery held fixed; θ moves through the live issuance engine."""
    if thetas is None:
        thetas = np.linspace(0.0, 1.5, 16)
    rows = []
    for theta in thetas:
        sov = Sovereign(sigma_X=0.0, sigma_eps=0.0, jump_prob=0.0)
        caster = _forecaster(n_paths=128)
        result = run(
            price_target(),
            T=1,
            seed=41,
            sovereign=sov,
            forecaster=caster,
            S0=0.8,
            X_path=np.ones(1),
            eps_path=np.zeros(1),
            theta_override=np.asarray([theta]),
            n_grid=9,
        )
        rec = result.records[0]
        p_P = float(rec["p_P"][0])
        p_Q = float(rec["p_Q"][0])
        u_P = float(-np.log(p_P))
        u_Q = float(-np.log(p_Q))
        rows.append(
            {
                "theta": float(theta),
                "u_P": u_P,
                "u_Q": u_Q,
                "premium_component": float(np.log(1.0 + theta)),
                "p_Q": p_Q,
                "ell": rec["ell"],
                "U": rec["U"],
                "issued_face": rec["issued_face"],
                "ceiling_binds": bool(rec["ceiling_binds"]),
            }
        )
    return {"rows": rows, "identity_gap": max(abs(r["u_Q"] - r["u_P"] - r["premium_component"]) for r in rows)}


def e6_manipulation(zetas: np.ndarray | None = None, T: int = 16, seed: int = 9) -> dict:
    if zetas is None:
        zetas = np.array([0.0, 0.05, 0.1, 0.2, 0.4])
    sov = Sovereign()
    X, eps = _paths(T, seed, sov)
    caster = _forecaster()
    beta = float(np.exp(-0.03))
    out = []
    for zeta in zetas:
        cfg = price_target()
        cfg = replace(
            cfg,
            zeta=float(zeta),
            attack_budget_ratio=1.0,
            name=f"zeta_{zeta}",
        )
        result = run(cfg, T=T, seed=seed, sovereign=sov, forecaster=caster, X_path=X, eps_path=eps, n_grid=6)
        Y = result.series("Y")
        discount = beta ** np.arange(T)
        # Endowment depth equals the exergy it was actually paid.
        W = float(result.series("W")[-1])
        out.append(
            {
                "zeta": float(zeta),
                "discounted_Y": float(np.sum(discount * Y)),
                "W": W,
                "bias": float(np.mean(result.series("market_bias"))),
                "issuance_gained": float(np.sum(np.maximum(result.series("issued_face"), 0.0))),
                "defense_spend": float(np.sum(result.series("defense_spend"))),
            }
        )
    return {"rows": out}


def e7_run(T: int = 24, seed: int = 6) -> dict:
    sov = Sovereign(lam=0.08)
    X, eps = _paths(T, seed, sov)
    caster = _forecaster()
    specs = {
        "target": price_target(),
        "target_reflexive": replace(
            price_target(), reflexive=True, market_weight=0.45, name="target_reflexive"
        ),
        "brake": v1_brake(),
        "brake_reflexive": replace(
            v1_brake(), reflexive=True, market_weight=0.45, name="brake_reflexive"
        ),
    }
    out = {}
    trigger = specs["target"].reflexive_at
    for name, cfg in specs.items():
        result = run(cfg, T=T, seed=seed, sovereign=sov, forecaster=caster, X_path=X, eps_path=eps, n_grid=6)
        M = result.series("M")
        out[name] = {
            "M": M,
            "P_gap": result.series("P_gap"),
            "p_bar": result.series("p_bar"),
            "S": result.series("S"),
            "multiplicity": result.multiplicity_periods,
            "M_change_after_trigger": float(M[-1] - M[min(trigger, T - 1)]),
        }
    return out


def e3_headline(T: int = 24, seed: int = 11) -> dict:
    sov = Sovereign(lam=0.1, jump_prob=0.08, jump_size=0.28)
    X, eps = _paths(T, seed, sov)
    # A deeper dip in the middle, shared by every policy, so the comparison is one shock.
    eps = eps.copy()
    eps[8:12] -= 0.12
    caster = _forecaster()
    policies = {
        "brake": v1_brake(),
        "target": price_target(),
        "repair": price_target_repair(),
    }
    out = {"policies": {}}
    for name, cfg in policies.items():
        result = run(cfg, T=T, seed=seed, sovereign=sov, forecaster=caster, X_path=X, eps_path=eps, n_grid=6)
        Y = result.series("Y")
        gap = result.series("P_gap")
        discount = np.exp(-0.03) ** np.arange(T)
        out["policies"][name] = {
            "P_gap": gap,
            "M": result.series("M"),
            "S": result.series("S"),
            "Y": Y,
            "discounted_Y": float(np.sum(discount * Y)),
            "final_S": float(result.series("S")[-1]),
            "mean_abs_gap": float(np.nanmean(np.abs(gap))),
            "phi": result.series("phi"),
            "issued_face": result.series("issued_face"),
            "retired_money": result.series("retired_money"),
            "multiplicity": result.multiplicity_periods,
        }
    # Relief lag and sensitivity, repair policy only.
    sweep = []
    for k in (1, 2, 4):
        for rho in (0.2, 0.8, 1.6):
            cfg = replace(price_target_repair(), k=k, rho=rho)
            result = run(cfg, T=T, seed=seed, sovereign=sov, forecaster=caster, X_path=X, eps_path=eps, n_grid=5)
            Y = result.series("Y")
            sweep.append(
                {
                    "k": k,
                    "rho": rho,
                    "discounted_Y": float(np.sum((np.exp(-0.03) ** np.arange(T)) * Y)),
                    "final_S": float(result.series("S")[-1]),
                    "mean_abs_gap": float(np.nanmean(np.abs(result.series("P_gap")))),
                }
            )
    out["sweep"] = sweep
    return out


def e9_bridge(shares: np.ndarray | None = None, n: int = 300, H: int = 5, seed: int = 0) -> dict:
    if shares is None:
        shares = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
    rows = []
    for share in shares:
        row = coupled_bridge(float(share), n_paths=n, horizon=H, seed=seed)
        row.pop("phi_j")
        row.pop("phi_k")
        row["claim"] = {"q": row["claim"].q, "maturity": row["claim"].maturity}
        row["surprisal_gap"] = float(
            -np.log(max(row["joint_price"], 1e-12))
            + np.log(max(row["marginal_price"], 1e-12))
        )
        rows.append(row)
    return {"rows": rows}


def e10_bakeoff(T: int = 20, seed: int = 13) -> dict:
    sov = Sovereign(lam=0.1, jump_prob=0.06, jump_size=0.22)
    X, eps = _paths(T, seed, sov)
    caster = _forecaster()
    rules = {
        "B1": 0.80,
        "B2": 0.50,
        "B3": 0.40,
    }
    out = {}
    for rule, ceiling in rules.items():
        base = replace(price_target(), rule=rule, B_bar_0=ceiling, name=rule)
        scales = {}
        for factor in (0.5, 1.0, 2.0):
            cfg = replace(base, B_bar_0=ceiling * factor)
            result = run(cfg, T=T, seed=seed, sovereign=sov, forecaster=caster, X_path=X, eps_path=eps, n_grid=6)
            Y = result.series("Y")
            gap = result.series("P_gap")
            phi = result.series("phi")
            scales[factor] = {
                "mean_abs_gap": float(np.nanmean(np.abs(gap))),
                "discounted_Y": float(np.sum((np.exp(-0.03) ** np.arange(T)) * Y)),
                "ceiling_frequency": float(np.mean(result.series("ceiling_binds"))),
                "default_frequency": float(np.mean(phi < 1.0 - 1e-8)),
            }
        out[rule] = scales
    return out


def e3_ensemble(seeds=range(20), T: int = 24) -> dict:
    """Common-random-number evidence for the headline policy comparison."""
    rows: dict[str, list[dict]] = {}
    for seed in seeds:
        sov = Sovereign(lam=0.1, jump_prob=0.08, jump_size=0.28)
        X, eps = _paths(T, int(seed), sov)
        eps = eps.copy()
        eps[8:12] -= 0.12
        policies = {
            "brake": v1_brake(),
            "target": price_target(),
            "repair": price_target_repair(),
            "target_linear": replace(price_target(), ell_form="linear"),
        }
        for name, cfg in policies.items():
            result = run(
                cfg,
                T=T,
                seed=int(seed),
                sovereign=sov,
                forecaster=_forecaster(),
                X_path=X,
                eps_path=eps,
                n_grid=5,
            )
            rows.setdefault(name, []).append(
                {
                    "discounted_Y": float(
                        np.sum(np.exp(-0.03) ** np.arange(T) * result.series("Y"))
                    ),
                    "mean_abs_gap": float(np.nanmean(np.abs(result.series("P_gap")))),
                    "final_S": float(result.series("S")[-1]),
                    "nonconvergence": float(np.mean(~result.series("solver_converged").astype(bool))),
                }
            )
    return {
        name: {
            metric: _interval([row[metric] for row in policy_rows])
            for metric in policy_rows[0]
        }
        for name, policy_rows in rows.items()
    }


def regime_ensemble(seeds=range(20), T: int = 20) -> dict:
    rows = {"R1": [], "R2": []}
    for seed in seeds:
        base = Sovereign(lam=0.1, jump_prob=0.08, jump_size=0.28)
        X, eps = _paths(T, int(seed), base)
        for regime in rows:
            sov = replace(base, regime=regime)
            result = run(
                price_target(),
                T=T,
                seed=int(seed),
                sovereign=sov,
                forecaster=_forecaster(),
                X_path=X,
                eps_path=eps,
                n_grid=5,
            )
            rows[regime].append(float(np.mean(result.series("phi") < 0.95)))
    return {regime: _interval(values) for regime, values in rows.items()}


def e10_ensemble(seeds=range(20), T: int = 20) -> dict:
    ceilings = {"B1": 0.80, "B2": 0.50, "B3": 0.40}
    rows: dict[str, list[dict]] = {rule: [] for rule in ceilings}
    for seed in seeds:
        sov = Sovereign(lam=0.1, jump_prob=0.06, jump_size=0.22)
        X, eps = _paths(T, int(seed), sov)
        for rule, ceiling in ceilings.items():
            cfg = replace(price_target(), rule=rule, B_bar_0=ceiling)
            result = run(
                cfg,
                T=T,
                seed=int(seed),
                sovereign=sov,
                forecaster=_forecaster(),
                X_path=X,
                eps_path=eps,
                n_grid=5,
            )
            rows[rule].append(
                {
                    "mean_abs_gap": float(np.nanmean(np.abs(result.series("P_gap")))),
                    "discounted_Y": float(
                        np.sum(np.exp(-0.03) ** np.arange(T) * result.series("Y"))
                    ),
                    "ceiling_frequency": float(np.mean(result.series("ceiling_binds"))),
                    "default_frequency": float(np.mean(result.series("phi") < 0.95)),
                }
            )
    return {
        rule: {
            metric: _interval([row[metric] for row in rule_rows])
            for metric in rule_rows[0]
        }
        for rule, rule_rows in rows.items()
    }


def calibration(n: int = 40, horizon: int = 6, seed: int = 3) -> dict:
    """Bin p^P against realised φ. Also record the realised wedge p^P − p^Q."""
    from sim.forecaster import _realise, brier_score
    from sim.model import Economy, NoteBook

    caster = _forecaster(n_paths=16)
    rng = np.random.default_rng(seed)
    forecast_p = []
    realised = []
    wedges = []
    for _ in range(n):
        # Include weak structures. A sample concentrated near S=1 only ever
        # realises φ≈1, and a reliability plot of that sample cannot speak.
        sov = Sovereign(jump_prob=0.15, jump_size=0.35, lam=0.12)
        state = Economy(sovereign=sov, S=float(rng.uniform(0.15, 0.9)), lam=sov.lam)
        state.theta = float(rng.uniform(0.0, 0.3))
        state.reflexive_factor = 1.0
        book = NoteBook()
        book.mint(0.15, 3)

        class _P:
            X_m_share = 0.25
            L_share = 0.0
            q_probe = 0.05

        horizons = list(range(1, horizon + 1))
        cast = caster.forecast(state, book, _P(), horizons, np.random.default_rng(int(rng.integers(1, 2**31 - 1))))
        actual = _realise(state, book, _P(), horizons, rng)
        forecast_p.extend(cast.p_P.tolist())
        realised.extend(actual.tolist())
        wedges.extend((cast.p_P - cast.p_Q).tolist())
    forecast_p = np.asarray(forecast_p)
    realised = np.asarray(realised)
    bins = np.linspace(0.0, 1.0, 6)
    centers = []
    freq = []
    for lo, hi in zip(bins[:-1], bins[1:]):
        mask = (forecast_p >= lo) & (forecast_p < hi if hi < 1 else forecast_p <= hi)
        if np.any(mask):
            centers.append(float(forecast_p[mask].mean()))
            freq.append(float(realised[mask].mean()))
    return {
        "brier": brier_score(caster, n_origins=20, horizon=horizon, seed=seed),
        "centers": centers,
        "frequencies": freq,
        "mean_wedge": float(np.mean(wedges)),
    }
