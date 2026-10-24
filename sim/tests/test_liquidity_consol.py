"""Contract tests for the adversarial liquidity-consol probes."""

from __future__ import annotations

import pytest

from sim.liquidity_consol import ConsolConfig, compare_collateral, simulate_liquidity_consol
from sim.probe_prediction_markets import _calibration, _snapshot


def test_native_collateral_adds_wrong_way_recovery_risk():
    config = ConsolConfig(paths=256, periods=12, seed=4)
    comparison = compare_collateral(config)
    external = comparison["external"]
    native = comparison["native"]
    assert native["mean_reserve_value"] < external["mean_reserve_value"]
    assert native["mean_recovery"] <= external["mean_recovery"]
    assert native["recovery_p10"] <= external["recovery_p10"]


def test_fixed_spread_depth_has_adverse_selection_cost():
    config = ConsolConfig(
        paths=256,
        periods=10,
        seed=7,
        fee_rate=0.0,
        manipulation_rate=0.0,
        oracle_failure_probability=0.0,
    )
    result = simulate_liquidity_consol("external", config)
    assert result["mean_adverse_selection_loss"] > 0.0
    assert result["mean_fees"] == pytest.approx(0.0)
    assert result["mean_final_capital"] < config.initial_capital


def test_history_snapshot_rejects_stale_observation():
    history = [{"t": 100, "p": 0.2}, {"t": 200, "p": 0.3}]
    assert _snapshot(history, target=250, horizon_days=1)["price"] == pytest.approx(0.3)
    assert _snapshot(history, target=250 + 3 * 86_400, horizon_days=1) is None


def test_calibration_summary_is_weighted_and_bounded():
    summary = _calibration([(0.1, 0.0), (0.9, 1.0), (0.6, 0.0)])
    assert summary["n"] == 3
    assert 0.0 <= summary["brier"] <= 1.0
    assert 0.0 <= summary["expected_calibration_error"] <= 1.0
    assert sum(row["n"] for row in summary["bins"]) == 3
