"""Contract tests that keep E5--E9 wired to their advertised mechanisms."""

from __future__ import annotations

import numpy as np

from sim.experiments import e5_premium, e6_manipulation, e8_growth, e9_bridge


def test_e5_runs_live_issuance_window():
    out = e5_premium(np.asarray([0.0, 0.8]))
    assert all("issued_face" in row and "U" in row for row in out["rows"])
    assert out["rows"][1]["ell"] < out["rows"][0]["ell"]


def test_e6_reports_live_market_and_real_costs():
    out = e6_manipulation(np.asarray([0.0, 0.1]), T=3, seed=2)
    assert all("issuance_gained" in row and "defense_spend" in row for row in out["rows"])
    assert out["rows"][1]["W"] >= 0.0


def test_e8_is_perp_inclusive_and_uses_empirical_kl():
    out = e8_growth(T=4, seed=3)
    assert out["M"][0] > 0.0
    assert np.all(np.isfinite(out["kl"]))


def test_e9_has_joint_price_and_capacity():
    out = e9_bridge(np.asarray([0.0, 0.5]), n=128, H=3, seed=1)
    assert all("joint_capacity" in row and "capacity_gap" in row for row in out["rows"])
