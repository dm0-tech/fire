"""Single-issuer and two-issuer simulation loop. No plotting."""

from __future__ import annotations

from dataclasses import dataclass, field
import math

import numpy as np

from sim.demand import confidence, damped_fixed_point, ell, find_sign_changes, price_level, select_root
from sim.manipulation import levy, manipulate
from sim.measures import (
    bernoulli_kl,
    book_functional_with_perps,
    joint_surprisal,
    mean_horizon_kl,
    surprisal,
)
from sim.model import Economy, NoteBook, Sovereign, allocate, draw_X, draw_eps, step_S, step_theta
from sim.policies import LADDERS, Obs, PolicyConfig, ladder_allocations, maintenance_share

_EPS = 1e-8
B_FLOOR = 0.02


def _should_penalize_r2(regime: str, maturing_quantity: float, phi: float) -> bool:
    return regime == "R2" and maturing_quantity > 0 and phi < 1.0 - 1e-12


@dataclass
class _View:
    X_m_share: float
    L_share: float
    q_probe: float
    market_weight: float = 0.0


@dataclass
class RunResult:
    records: list[dict] = field(default_factory=list)
    config: PolicyConfig | None = None
    multiplicity_periods: list[int] = field(default_factory=list)

    def series(self, key: str) -> np.ndarray:
        return np.asarray([r[key] for r in self.records], dtype=float)


def _p_lookup(forecast):
    def p_Q(maturity):
        return forecast.at(maturity, "Q")

    return p_Q


def _functional(book: NoteBook, t: int, beta: float, forecast, rule: str) -> float:
    rows = []
    perps = []
    for n in book.notes:
        if n.maturity is None:
            perps.append(n.q)
        elif n.maturity >= t:
            rows.append((n.q, n.maturity))
    return book_functional_with_perps(
        rows, perps, lambda m: forecast.at(m, "Q"), t, beta, rule
    )


def _mint_ladder(book: NoteBook, t: int, lags: tuple[int, ...], scale: float) -> list[tuple[float, int]]:
    minted = []
    for quantity, lag in ladder_allocations(lags, scale):
        book.mint(quantity, t + lag)
        minted.append((quantity, t + lag))
    return minted


def _ceiling(config: PolicyConfig, A: float) -> float:
    if not config.repair:
        return config.B_bar_0
    return max(B_FLOOR, config.B_bar_0 * (1.0 + config.rho * A))


def _accrual(t: int, beta: float, realised: dict[int, float], forecasts: dict[int, dict[int, float]], k: int) -> float:
    A = 0.0
    for j, phi in realised.items():
        if j >= t:
            continue
        made = forecasts.get(j - k)
        if not made or j not in made:
            continue
        A += (beta ** (t - j)) * (phi - made[j])
    return A


def run(
    config: PolicyConfig,
    T: int = 40,
    seed: int = 0,
    sovereign: Sovereign | None = None,
    forecaster=None,
    S0: float = 0.75,
    X_path: np.ndarray | None = None,
    eps_path: np.ndarray | None = None,
    theta_override: np.ndarray | None = None,
    ell_bar: float = 1.0,
    p_star: float = 0.75,
    tau_ell: float = 0.08,
    P_star: float = 1.0,
    delta: float = 0.03,
    n_grid: int = 9,
) -> RunResult:
    """Simulate T periods.

    `X_path` and `eps_path`, when supplied, are the realised shocks. They are
    never passed into the forecaster. `theta_override` replaces the premium
    process, which is how E5 shocks θ alone.
    """
    if forecaster is None:
        from sim.forecaster import Forecaster

        forecaster = Forecaster()
    sov = sovereign or Sovereign()
    economy = Economy(sovereign=sov, delta=delta, S=S0, lam=sov.lam)
    rng = np.random.default_rng(seed)
    # A second generator so forecast draws cannot consume the realised-shock stream.
    forecast_rng = np.random.default_rng(rng.integers(1, 2**31 - 1))
    beta = economy.beta
    theta = 0.04
    result = RunResult(config=config)
    realised: dict[int, float] = {}
    forecasts: dict[int, dict[int, float]] = {}
    prev_scale = 0.0
    ceiling_bound_last = False
    W = 0.0
    horizons_ahead = 16
    secondary_prices: dict[int, float] = {}
    if config.perp_payment > 0:
        economy.book.mint(config.perp_payment, None)

    for t in range(T):
        economy.t = t
        if theta_override is not None:
            theta = float(theta_override[t])
        if X_path is not None:
            X = float(X_path[t])
        else:
            X = float(draw_X(rng, 1, sov.X_mean, sov.sigma_X)[0])
        A = _accrual(t, beta, realised, forecasts, config.k)
        B_bar = _ceiling(config, A)
        share = maintenance_share(
            config.maintenance,
            Obs(t=t, S=economy.S, X=X, ceiling_bound_last=ceiling_bound_last, base_share=config.base_share),
        )
        X_m_desired = share * X
        q_probe = 0.05 * sov.X_mean
        state = economy
        state.theta = theta
        state.secondary_prices = secondary_prices  # type: ignore[attr-defined]
        state.current_X = X  # type: ignore[attr-defined]
        state.current_X_m = X_m_desired  # type: ignore[attr-defined]

        horizons = [t + h for h in range(1, horizons_ahead + 1)]
        chosen_lags = LADDERS[0]
        chosen_scale = 0.0
        chosen_forecast = None
        roots: list[float] = []
        feasible_scales: list[float] = []
        residuals: list[float] = []
        bound = False
        solver_iterations = 0
        solver_converged = False
        solver_fallback = False
        retired = []

        def market_adjust(forecast):
            if config.attack_budget_ratio <= 0:
                return 0.0, 0.0
            biases = []
            spent = []
            for i, fair in enumerate(forecast.p_Q.copy()):
                attack = manipulate(
                    float(fair),
                    attacker_budget=config.attack_budget_ratio * max(W, 0.02),
                    endowment=W,
                )
                target = float(attack["p_final"])
                forecast.p_Q[i] = target
                if getattr(forecast, "phi_P", None) is not None:
                    samples = np.asarray(forecast.phi_P[:, i], dtype=float)
                    mean = float(samples.mean())
                    if target <= mean:
                        mapped = samples * (target / mean) if mean > 0 else np.zeros_like(samples)
                    elif mean < 1.0:
                        mapped = samples + ((target - mean) / (1.0 - mean)) * (1.0 - samples)
                    else:
                        mapped = np.full_like(samples, target)
                    forecast.phi_Q[:, i] = mapped
                biases.append(attack["bias"])
                spent.append(attack["spent_defence"])
            forecast.market_bias = float(np.mean(biases))  # type: ignore[attr-defined]
            forecast.defense_spend = float(np.mean(spent))  # type: ignore[attr-defined]
            return forecast.market_bias, forecast.defense_spend  # type: ignore[attr-defined]

        def evaluate(lags, scale, forecast):
            trial = economy.book.copy()
            minted = _mint_ladder(trial, t, lags, scale) if scale > 0 else []
            retired = trial.retire_money(-scale, t, beta) if scale < 0 and config.allow_retirement else []
            p_of = _p_lookup(forecast)
            rows = [(q, t + lag) for q, lag in ((q, m - t) for q, m in minted)]
            L = levy([(q, p_of(t + lag), lag) for q, lag in ((q, m - t) for q, m in minted)], config.zeta, beta) if minted else 0.0
            R_requested = 0.0
            for q, maturity in retired:
                if maturity is None:
                    R_requested += q * p_of(None) * beta / (1.0 - beta)
                else:
                    lag = max(0, maturity - t)
                    R_requested += q * p_of(maturity) * beta**lag
            Q = trial.maturing_quantity(t)
            alloc = allocate(X, X_m_desired, L, Q, economy.S, sov.S_min, sov.regime, R_requested)
            if retired and R_requested > 0 and alloc["R"] < R_requested - 1e-10:
                # Only claims actually bought back may leave the book.
                paid_fraction = alloc["R"] / R_requested
                trial = economy.book.copy()
                retired = trial.retire_money((-scale) * paid_fraction, t, beta)
                Q = trial.maturing_quantity(t)
                alloc = allocate(
                    X, X_m_desired, L, Q, economy.S, sov.S_min, sov.regime, alloc["R"]
                )
            U = _functional(trial, t, beta, forecast, config.rule)
            return trial, alloc, U, L, retired

        # One forecast of the current book sets the curve; scale changes quantities
        # and a second forecast is taken at the chosen book so the quote stays quantity-conditional.
        view = _View(share, min(0.5, config.zeta), q_probe, config.market_weight)
        base_forecast = forecaster.forecast(state, economy.book, view, horizons, forecast_rng)
        market_adjust(base_forecast)

        best = None
        best_gap = math.inf
        # One shock seed per period so the grid varies quantity, not Monte Carlo noise.
        period_seed = int(forecast_rng.integers(1, 2**31 - 1))
        for lags in LADDERS:
            min_action = -economy.book.money_stock(t, beta) if config.allow_retirement else 0.0
            scales = np.linspace(min_action, sov.X_mean, max(n_grid * 2 - 1, 3))
            local_scales = []
            local_resid = []
            local_forecasts = []
            for scale in scales:
                trial_book = economy.book.copy()
                if scale > 0:
                    _mint_ladder(trial_book, t, lags, float(scale))
                elif scale < 0 and config.allow_retirement:
                    trial_book.retire_money(-float(scale), t, beta)
                cast = forecaster.forecast(
                    state, trial_book, view, horizons, np.random.default_rng(period_seed)
                )
                market_adjust(cast)
                trial, alloc, U, L, retired = evaluate(lags, float(scale), cast)
                if U > B_bar + 1e-8:
                    continue
                p_bar = confidence(trial, t, beta, _p_lookup(cast), horizons)
                e_val = ell(p_bar, ell_bar, p_star, tau_ell, config.ell_form)
                M = trial.money_stock(t, beta)
                if config.issuance == "fill_ceiling":
                    residual = -float(scale)
                else:
                    M_target = P_star * e_val * alloc["Y"]
                    residual = M - M_target
                local_scales.append(float(scale))
                local_resid.append(residual)
                local_forecasts.append((cast, trial, alloc, U, L, p_bar, e_val, M, retired))
            if not local_scales:
                continue
            if config.issuance == "fill_ceiling":
                pick = int(np.argmin(local_resid))
                chosen_scale = local_scales[pick]
                chosen_forecast, trial, alloc, U, L, p_bar, e_val, M, retired = local_forecasts[pick]
                bound = chosen_scale < scales[-1] - 1e-9 or lags != LADDERS[0]
                roots = [chosen_scale]
                solver_converged = True
                best = (trial, alloc, U, L, p_bar, e_val, M, chosen_forecast, chosen_scale, roots, bound, retired)
                break
            sign_roots = find_sign_changes(local_scales, local_resid)
            solve = damped_fixed_point(
                lambda action: float(np.interp(action, local_scales, local_resid)),
                prev_scale,
                local_scales[0],
                local_scales[-1],
            )
            solver_iterations = int(solve["iterations"])
            solver_converged = bool(solve["converged"])
            if solver_converged:
                scale_star = float(solve["value"])
                bound = False
            elif sign_roots:
                scale_star, _ = select_root(sign_roots, prev_scale)
                solver_fallback = True
                bound = False
            elif local_resid[0] > 0:
                scale_star = local_scales[0]
                solver_fallback = True
                bound = False
            else:
                scale_star = local_scales[-1]
                solver_fallback = True
                bound = True
            # Mint at the interpolated root, not at the nearest grid node.
            trial_book = economy.book.copy()
            if scale_star > 0:
                _mint_ladder(trial_book, t, lags, float(scale_star))
            elif scale_star < 0 and config.allow_retirement:
                trial_book.retire_money(-float(scale_star), t, beta)
            cast = forecaster.forecast(
                state, trial_book, view, horizons, np.random.default_rng(period_seed)
            )
            market_adjust(cast)
            trial, alloc, U, L, retired = evaluate(lags, float(scale_star), cast)
            if U > B_bar + 1e-8:
                # The root sits past the ceiling. Fall back to the largest feasible grid node.
                pick = len(local_scales) - 1
                chosen_forecast, trial, alloc, U, L, p_bar, e_val, M, retired = local_forecasts[pick]
                chosen_scale = local_scales[pick]
                bound = True
            else:
                p_bar = confidence(trial, t, beta, _p_lookup(cast), horizons)
                e_val = ell(p_bar, ell_bar, p_star, tau_ell, config.ell_form)
                M = trial.money_stock(t, beta)
                chosen_forecast = cast
                chosen_scale = float(scale_star)
            M_target = P_star * e_val * alloc["Y"]
            gap = abs(M - M_target)
            if best is None or gap < best_gap - 1e-8:
                best_gap = gap
                roots = sign_roots
                best = (trial, alloc, U, L, p_bar, e_val, M, chosen_forecast, chosen_scale, roots, bound, retired)
            if sign_roots or local_resid[0] > 0:
                break

        if best is None:
            # No feasible mint. Deliver what is already outstanding.
            cast = base_forecast
            Q = economy.book.maturing_quantity(t)
            alloc = allocate(X, X_m_desired, 0.0, Q, economy.S, sov.S_min, sov.regime)
            p_bar = confidence(economy.book, t, beta, _p_lookup(cast), horizons)
            e_val = ell(p_bar, ell_bar, p_star, tau_ell, config.ell_form)
            M = economy.book.money_stock(t, beta)
            U = _functional(economy.book, t, beta, cast, config.rule)
            L = 0.0
            trial = economy.book
            chosen_forecast = cast
            bound = True
            chosen_scale = 0.0
            roots = []
            retired = []
        else:
            trial, alloc, U, L, p_bar, e_val, M, cast, chosen_scale, roots, bound, retired = best

        if len(roots) > 1:
            result.multiplicity_periods.append(t)

        economy.book = trial
        P = price_level(M, e_val, alloc["Y"])
        phi = alloc["phi"]
        realised[t] = phi
        forecasts[t] = {int(h): cast.at(int(h), "Q") for h in cast.horizons}
        # Institutional damage only on structural failure.
        if _should_penalize_r2(sov.regime, alloc["Q_maturity"], phi):
            economy.lam = min(0.95, economy.lam + sov.delta_lam)
        defense_spend = float(getattr(cast, "defense_spend", 0.0))
        market_bias = float(getattr(cast, "market_bias", 0.0))
        W = max(0.0, W + L - defense_spend)
        u_curve = [float(surprisal(cast.at(h, "Q"))) for h in cast.horizons]
        p_curve = [cast.at(h, "Q") for h in cast.horizons]
        pP_curve = [cast.at(h, "P") for h in cast.horizons]
        record = {
            "t": t,
            "S": economy.S,
            "X": X,
            "X_p": alloc["X_p"],
            "X_m": alloc["X_m"],
            "D": alloc["D"],
            "D_maturity": alloc["D_maturity"],
            "R": alloc["R"],
            "L": L,
            "Y": alloc["Y"],
            "phi": phi,
            "Q": alloc["Q"],
            "M": M,
            "P": P if np.isfinite(P) else np.nan,
            "P_gap": (P / P_star - 1.0) if np.isfinite(P) else np.nan,
            "p_bar": p_bar,
            "ell": e_val,
            "U": U,
            "B_bar": B_bar,
            "A": A,
            "theta": theta,
            "ceiling_binds": bound or U > B_bar - 1e-6 and chosen_scale == 0.0,
            "scale": chosen_scale,
            "issued_face": max(0.0, chosen_scale),
            "retired_money": max(0.0, -chosen_scale),
            "retired_face": float(sum(q for q, _ in retired)),
            "n_roots": len(roots),
            "solver_iterations": solver_iterations,
            "solver_converged": solver_converged,
            "solver_fallback": solver_fallback,
            "W": W,
            "market_bias": market_bias,
            "defense_spend": defense_spend,
            "u": u_curve,
            "p_Q": p_curve,
            "p_P": pP_curve,
            "horizons": list(map(int, cast.horizons)),
            "kl_bernoulli": float(np.mean([bernoulli_kl(a, b) for a, b in zip(pP_curve, p_curve)])),
        }
        phi_P = getattr(cast, "phi_P", None)
        phi_Q = getattr(cast, "phi_Q", None)
        if phi_P is not None and phi_Q is not None:
            active = [
                i
                for i, h in enumerate(cast.horizons)
                if trial.quantity_at(int(h)) > 0
            ]
            physical_paths = np.asarray(phi_P)[:, active]
            joint_u, joint_p = joint_surprisal(physical_paths, eta=0.05)
            if active:
                marginal_success = np.mean(physical_paths >= 0.95, axis=0)
                additive_u = float(np.sum(surprisal(marginal_success)))
            else:
                additive_u = 0.0
            record["U_joint"] = joint_u
            record["p_joint"] = joint_p
            record["joint_ratio"] = joint_u / additive_u if additive_u > 0 else 1.0
            record["U_joint_additive"] = additive_u
            record["U_joint_measure"] = "P"
            record["kl_empirical"] = mean_horizon_kl(phi_P, phi_Q)
        else:
            record.update(U_joint=np.nan, p_joint=np.nan, joint_ratio=np.nan, kl_empirical=np.nan)
        record["kl"] = record["kl_empirical"]
        if config.issuance != "fill_ceiling":
            target_residual = M - P_star * e_val * alloc["Y"]
            record["solver_residual"] = target_residual
            record["solver_converged"] = abs(target_residual) <= 1e-3
        else:
            record["solver_residual"] = np.nan
        # Accounting identity must hold on the realised split.
        record["account_gap"] = alloc["X_p"] + alloc["X_m"] + alloc["D"] + alloc["L"] - X
        result.records.append(record)
        secondary_prices = {
            int(h): float(cast.at(int(h), "Q")) * beta ** max(1, int(h) - t)
            for h in cast.horizons
        }
        if config.reflexive and t >= config.reflexive_at:
            secondary_prices = {h: p * config.exit_haircut for h, p in secondary_prices.items()}
        ceiling_bound_last = bool(record["ceiling_binds"])
        prev_scale = chosen_scale

        economy.book.extinguish_matured(t)
        if eps_path is not None:
            eps = float(eps_path[t])
        else:
            crisis = np.array([economy.in_crisis])
            eps = float(
                draw_eps(rng, 1, sov.sigma_eps, sov.jump_prob, sov.jump_size, crisis, sov.crisis_jump)[0]
            )
        economy.S = step_S(economy.S, alloc["X_m"], economy.lam, sov.kappa, eps)
        if sov.p_enter > 0 or economy.in_crisis:
            economy.step_crisis(rng)
        if theta_override is None:
            theta = step_theta(theta, economy.S, rng)
        state.theta = theta

    return result
