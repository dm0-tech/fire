"""Specification tests. These encode section 4.4, not the private arithmetic of an implementation."""

from __future__ import annotations

import inspect

import numpy as np
import pytest

from sim.bridge import coupled_bridge
from sim.demand import confidence, damped_fixed_point, ell_linear, ell_threshold, find_sign_changes, price_level
from sim.forecasters.mc import MonteCarloForecaster
from sim.measures import (
    U0,
    U1,
    U2,
    U3,
    closed_form_perp_B1,
    book_functional_with_perps,
    empirical_kl,
    mean_horizon_kl,
    hazard,
    joint_surprisal,
    perp_partial,
    positive_dependence_gap,
    surprisal,
    yield_curve,
)
from sim.model import NoteBook, Sovereign, allocate, draw_eps, g, psi, step_S
from sim.policies import ladder_allocations, price_target
from sim.engine import _should_penalize_r2, run


def test_exergy_split_is_four_way():
    out = allocate(X=1.0, X_m=0.2, L=0.1, Q=0.4, S=0.8, S_min=0.45, regime="R1")
    assert out["X_p"] + out["X_m"] + out["D"] + out["L"] == pytest.approx(1.0)
    assert out["X_p"] >= 0 and out["D"] >= 0 and out["L"] >= 0 and out["X_m"] >= 0
    # The two-way identity from v1 does not hold once delivery and the levy are real.
    assert out["X_p"] + out["X_m"] != pytest.approx(1.0)


def test_delivery_does_not_exceed_promises_or_inflow():
    out = allocate(X=1.0, X_m=0.2, L=0.1, Q=5.0, S=1.0, S_min=0.45, regime="R1")
    assert out["D"] <= out["Q"] + 1e-12
    assert out["D"] <= out["room"] + 1e-12


def test_phi_is_one_only_when_structure_and_capacity_allow():
    full = allocate(X=2.0, X_m=0.1, L=0.0, Q=0.5, S=0.9, S_min=0.45, regime="R2")
    assert full["structural"] == 1.0
    assert full["Q"] <= full["room"]
    assert full["phi"] == pytest.approx(1.0)

    degraded = allocate(X=2.0, X_m=0.1, L=0.0, Q=0.5, S=0.2, S_min=0.45, regime="R2")
    assert degraded["structural"] == 0.0
    assert degraded["phi"] == pytest.approx(0.0)

    rationed = allocate(X=0.3, X_m=0.1, L=0.0, Q=5.0, S=0.9, S_min=0.45, regime="R2")
    assert rationed["structural"] == 1.0
    assert rationed["phi"] < 1.0

    soft = allocate(X=2.0, X_m=0.0, L=0.0, Q=0.2, S=0.225, S_min=0.45, regime="R1")
    assert soft["structural"] == pytest.approx(0.5)
    assert soft["phi"] == pytest.approx(0.5)


def test_constant_hazard_is_flat_yield_not_an_inversion():
    h = 0.04
    delta = 0.03
    maturities = np.arange(1, 25)
    p = np.exp(-h * maturities)
    u = surprisal(p)
    assert np.all(hazard(u) >= -1e-10)
    r = yield_curve(u, delta, maturities)
    assert np.allclose(r, delta + h, atol=1e-10)


def test_perp_b0_diverges_and_discounted_rules_converge():
    x, h, beta = 1.0, 0.05, 0.96
    short = perp_partial(x, h, beta, 40)
    mid = perp_partial(x, h, beta, 200)
    long = perp_partial(x, h, beta, 400)
    assert long["B0"][-1] > short["B0"][-1] * 10
    assert long["B0"][-1] > mid["B0"][-1] * 2
    closed = closed_form_perp_B1(x, h, beta)
    assert long["B1"][-1] == pytest.approx(closed, rel=0.02)
    # The discounted tail from 200 to 400 is negligible; B0's is not.
    assert abs(long["B1"][-1] - mid["B1"][-1]) < 0.01 * closed
    # B2 is bounded by the discounted quantity of the perp, x β / (1-β).
    assert long["B2"][-1] < x * beta / (1.0 - beta) + 1e-6
    assert abs(long["B2"][-1] - mid["B2"][-1]) < 0.01
    assert abs(long["B3"][-1] - mid["B3"][-1]) < 0.02


def test_ceiling_respected_after_issuance():
    caster = MonteCarloForecaster()
    caster.n_paths = 6
    result = run(price_target(), T=4, seed=3, forecaster=caster, n_grid=5)
    for row in result.records:
        assert row["U"] <= row["B_bar"] + 1e-6


def test_forecaster_signature_has_no_future_shocks():
    params = inspect.signature(MonteCarloForecaster.forecast).parameters
    names = " ".join(params)
    assert "future" not in names
    assert "eps_path" not in names
    assert "X_path" not in names
    src = inspect.getsource(MonteCarloForecaster.forecast)
    assert "eps_path" not in src
    assert "future_eps" not in src


def test_model_delivery_is_positively_dependent():
    rng = np.random.default_rng(0)
    sov = Sovereign()
    n, H = 400, 4
    S = np.full(n, 0.8)
    phi = np.zeros((n, H))
    for h in range(H):
        eps = draw_eps(rng, n, sov.sigma_eps, 0.3, 0.5)
        # A shared jump moves every horizon on a path together.
        for i in range(n):
            S[i] = step_S(S[i], 0.05, sov.lam, sov.kappa, float(eps[i]))
            structural = psi(float(S[i]), sov.S_min, "R2")
            phi[i, h] = structural
    gap = positive_dependence_gap(phi, eta=0.05)
    assert gap >= -1e-9

    # Negative dependence reverses the inequality. The test must not claim it always holds.
    anti = np.zeros((200, 2))
    anti[:100, 0] = 1.0
    anti[100:, 1] = 1.0
    assert positive_dependence_gap(anti, eta=0.05) < 0.0

    independent = np.array(
        [[a, b] for a in (0.0, 1.0) for b in (0.0, 1.0)] * 50
    )
    assert positive_dependence_gap(independent, eta=0.05) == pytest.approx(0.0)


def test_joint_surprisal_matches_the_event_probability():
    phi = np.array([[1.0, 1.0], [1.0, 0.0], [0.9, 1.0], [1.0, 1.0]])
    u, prob = joint_surprisal(phi, eta=0.05)
    assert prob == pytest.approx(0.5)
    assert u == pytest.approx(-np.log(0.5))


def test_money_market_identity():
    caster = MonteCarloForecaster()
    caster.n_paths = 6
    result = run(price_target(), T=3, seed=1, forecaster=caster, n_grid=5)
    for row in result.records:
        if row["ell"] * row["Y"] <= 0 or not np.isfinite(row["P"]):
            continue
        assert row["P"] * row["ell"] * row["Y"] == pytest.approx(row["M"], rel=1e-6, abs=1e-6)


def test_two_roots_are_both_reported():
    scales = [0.0, 1.0, 2.0, 3.0, 4.0]
    residuals = [-1.0, 1.0, -0.5, 0.2, 1.0]
    roots = find_sign_changes(scales, residuals)
    assert len(roots) >= 2


def test_g_and_liquidity_shapes():
    assert g(0.0, 1.2) == pytest.approx(0.0)
    assert g(1.0, 1.2) > g(0.2, 1.2)
    assert ell_threshold(0.99, 1.0, 0.75, 0.05) > ell_threshold(0.2, 1.0, 0.75, 0.05)
    assert ell_linear(0.4, 2.0) == pytest.approx(0.8)
    assert price_level(2.0, 0.5, 4.0) == pytest.approx(1.0)


def test_functionals_accept_a_constant_curve():
    q = np.array([1.0, 1.0])
    p = np.array([0.8, 0.5])
    u = surprisal(p)
    m = np.array([1.0, 2.0])
    beta = 0.9
    assert U0(q, u) == pytest.approx(np.sum(u))
    assert U1(q, u, beta, m) < U0(q, u)
    assert U2(q, p, beta, m) > 0
    assert U3(q, u, beta, m) == pytest.approx(np.sum(q * u * beta**m) / np.sum(q * beta**m))


def test_notebook_perp_stock():
    book = NoteBook()
    book.mint(2.0, None)
    beta = 0.9
    assert book.money_stock(0, beta) == pytest.approx(2.0 * beta / (1.0 - beta))
    book.mint(1.0, 3)
    assert book.maturing_quantity(3) == pytest.approx(3.0)  # dated note plus the perp
    book.extinguish_matured(3)
    assert book.maturing_quantity(3) == pytest.approx(2.0)


def test_total_face_is_split_across_ladder():
    allocations = ladder_allocations((1, 2, 4, 8, 16), 1.0)
    assert sum(q for q, _ in allocations) == pytest.approx(1.0)
    assert all(q == pytest.approx(0.2) for q, _ in allocations)


def test_empty_book_confidence_uses_probe_curve():
    book = NoteBook()
    assert confidence(book, 0, 0.95, lambda m: 0.6, [1, 2, 4]) == pytest.approx(0.6)


def test_retirement_is_real_and_shortest_first():
    book = NoteBook()
    book.mint(1.0, 1)
    book.mint(1.0, 4)
    retired = book.retire_money(0.5, 0, 0.9)
    assert retired[0][1] == 1
    assert book.money_stock(0, 0.9) == pytest.approx(0.4 + 0.9**4)


def test_perp_full_tail_and_b0_rejection():
    p = lambda maturity: np.exp(-0.05 * min(int(maturity), 16))
    b1 = book_functional_with_perps([], [1.0], p, 0, 0.96, "B1")
    assert np.isfinite(b1)
    assert book_functional_with_perps([], [1.0], p, 0, 0.96, "B0") == np.inf


def test_empirical_fractional_kl():
    samples = np.linspace(0.0, 1.0, 200)
    assert empirical_kl(samples, samples) == pytest.approx(0.0)
    assert empirical_kl(samples, samples**2) > 0.0
    p = np.column_stack([np.zeros(200), np.ones(200)])
    q = np.column_stack([np.ones(200), np.zeros(200)])
    assert empirical_kl(p, q) == pytest.approx(0.0)
    assert mean_horizon_kl(p, q) > 0.0


def test_hybrid_solver_reports_convergence():
    out = damped_fixed_point(lambda x: x - 0.4, 0.0, -1.0, 1.0)
    assert out["converged"]
    assert out["value"] == pytest.approx(0.4, abs=1e-4)


def test_forecaster_is_quantity_conditional_behaviorally():
    from sim.model import Economy

    caster = MonteCarloForecaster()
    caster.n_paths = 64
    state = Economy()
    state.theta = 0.04
    sparse = NoteBook()
    heavy = NoteBook()
    sparse.mint(0.05, 1)
    heavy.mint(2.0, 1)

    class Policy:
        X_m_share = 0.25
        L_share = 0.0
        q_probe = 0.05
        market_weight = 0.0

    a = caster.forecast(state, sparse, Policy(), [1], np.random.default_rng(4))
    b = caster.forecast(state, heavy, Policy(), [1], np.random.default_rng(4))
    assert b.p_P[0] < a.p_P[0]


def test_priced_samples_match_the_priced_mean():
    from sim.model import Economy

    caster = MonteCarloForecaster()
    caster.n_paths = 64
    state = Economy()
    state.theta = 0.1
    state.current_X_m = 0.25

    class Policy:
        X_m_share = 0.25
        L_share = 0.0
        q_probe = 0.05
        market_weight = 0.0

    cast = caster.forecast(
        state, NoteBook(), Policy(), [1, 2], np.random.default_rng(3)
    )
    assert cast.phi_Q.mean(axis=0) == pytest.approx(cast.p_Q, abs=1e-12)


def test_current_maintenance_conditions_next_horizon():
    from sim.model import Economy

    caster = MonteCarloForecaster()
    caster.n_paths = 128

    class Policy:
        X_m_share = 0.25
        L_share = 0.0
        q_probe = 0.05
        market_weight = 0.0

    low = Economy(S=0.2)
    high = Economy(S=0.2)
    low.theta = high.theta = 0.0
    low.current_X_m = 0.0
    high.current_X_m = 1.0
    a = caster.forecast(low, NoteBook(), Policy(), [1], np.random.default_rng(7))
    b = caster.forecast(high, NoteBook(), Policy(), [1], np.random.default_rng(7))
    assert b.p_P[0] > a.p_P[0]


def test_r2_capacity_default_triggers_penalty():
    assert _should_penalize_r2("R2", 1.0, 0.5)
    assert not _should_penalize_r2("R2", 0.0, 1.0)


def test_perp_confidence_aggregates_horizon_curve():
    book = NoteBook()
    book.mint(1.0, None)
    beta = 0.9
    value = confidence(book, 0, beta, lambda maturity: 1.0 / (1.0 + maturity))
    assert 0.0 < value < 0.5


def test_engine_records_joint_and_solver_diagnostics():
    caster = MonteCarloForecaster()
    caster.n_paths = 16
    result = run(price_target(), T=2, seed=5, forecaster=caster, n_grid=5)
    for row in result.records:
        assert np.isfinite(row["U_joint"])
        assert "joint_ratio" in row
        assert row["solver_iterations"] >= 0
        assert abs(row["account_gap"]) < 1e-8


def test_retirement_delivery_remains_bounded_by_current_claims():
    out = allocate(
        X=2.0, X_m=0.0, L=0.0, Q=0.2, S=1.0, S_min=0.45, regime="R2", R=0.8
    )
    assert out["D"] <= out["Q"]
    assert out["Q_maturity"] == pytest.approx(0.2)


def test_future_realised_paths_do_not_change_current_forecast():
    caster_a = MonteCarloForecaster()
    caster_b = MonteCarloForecaster()
    caster_a.n_paths = caster_b.n_paths = 16
    X = np.ones(3)
    first = run(
        price_target(),
        T=3,
        seed=8,
        forecaster=caster_a,
        X_path=X,
        eps_path=np.array([0.0, 0.0, 0.0]),
        n_grid=5,
    )
    second = run(
        price_target(),
        T=3,
        seed=8,
        forecaster=caster_b,
        X_path=X,
        eps_path=np.array([0.0, -0.8, 0.8]),
        n_grid=5,
    )
    assert first.records[0]["p_P"] == pytest.approx(second.records[0]["p_P"])


def test_coupled_bridge_has_explicit_capacity():
    row = coupled_bridge(0.5, n_paths=128, horizon=3, seed=2)
    assert row["claim"].maturity == 3
    assert row["joint_price"] > 0
    assert "capacity_gap" in row
