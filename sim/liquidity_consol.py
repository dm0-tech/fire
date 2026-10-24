"""Adversarial toy model for the liquidity-consol conjecture.

This is deliberately narrower than the sovereign engine.  A venue issues notes,
uses part of the proceeds as market-making capital, and promises redemption from
that capital plus a segregated reserve.  The reserve is either an external asset
or a venue token whose value falls with information shocks and venue impairment.

The market maker posts a stale fixed-spread quote.  Better-informed flow takes
the profitable side, making "neutral depth" a real subsidy rather than a free
balance-sheet label.  The issuer may also spend to bias its own persistence
quote upward; the induced note issuance is reported separately.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace

import numpy as np


@dataclass(frozen=True)
class ConsolConfig:
    periods: int = 52
    paths: int = 2_000
    seed: int = 17
    initial_capital: float = 1.0
    initial_reserve: float = 1.0
    initial_liability: float = 1.5
    initial_probability: float = 0.85
    spread: float = 0.04
    quote_size: float = 0.12
    inventory_limit: float = 0.60
    fee_rate: float = 0.01
    information_sigma: float = 0.10
    stress_probability: float = 0.06
    stress_logit_jump: float = 0.70
    withdrawal_floor: float = 0.20
    reserve_share_of_new_issuance: float = 0.65
    manipulation_rate: float = 0.003
    manipulation_impact: float = 0.30
    issuance_sensitivity: float = 0.30
    token_stress_beta: float = 0.25
    token_health_beta: float = 0.50
    oracle_failure_probability: float = 0.01
    oracle_loss_fraction: float = 0.25


def _logit(p: np.ndarray) -> np.ndarray:
    p = np.clip(p, 1e-9, 1.0 - 1e-9)
    return np.log(p / (1.0 - p))


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def simulate_liquidity_consol(
    collateral_mode: str,
    config: ConsolConfig | None = None,
) -> dict:
    """Run common-path external- or native-collateral venue notes.

    ``external`` keeps segregated reserve value fixed. ``native`` marks the
    reserve to a venue token that is exposed to the same shocks that drain the
    market-making endowment.  Both modes receive exactly the same random draws
    for a fixed seed.
    """

    if collateral_mode not in {"external", "native"}:
        raise ValueError("collateral_mode must be 'external' or 'native'")
    cfg = config or ConsolConfig()
    if cfg.periods <= 0 or cfg.paths <= 0:
        raise ValueError("periods and paths must be positive")

    rng = np.random.default_rng(cfg.seed)
    n = cfg.paths
    capital = np.full(n, cfg.initial_capital, dtype=float)
    reserve_units = np.full(n, cfg.initial_reserve, dtype=float)
    token_value = np.ones(n, dtype=float)
    liability = np.full(n, cfg.initial_liability, dtype=float)
    fair = np.full(n, cfg.initial_probability, dtype=float)
    stale_quote = fair.copy()
    active = np.ones(n, dtype=bool)
    inventory_yes = np.zeros(n)

    adverse_loss = np.zeros(n)
    inventory_pnl = np.zeros(n)
    fees = np.zeros(n)
    manipulation_spend = np.zeros(n)
    issuance_gained = np.zeros(n)
    oracle_loss = np.zeros(n)
    active_depth_periods = np.zeros(n)

    for _ in range(cfg.periods):
        capital_before = capital.copy()
        normal = rng.normal(0.0, cfg.information_sigma, size=n)
        stressed = rng.random(n) < cfg.stress_probability
        logit_move = normal - stressed * cfg.stress_logit_jump
        next_fair = _sigmoid(_logit(fair) + logit_move)
        period_inventory_pnl = inventory_yes * (next_fair - fair)
        capital += period_inventory_pnl
        inventory_pnl += period_inventory_pnl

        quoted_depth = np.where(
            active,
            np.minimum(cfg.quote_size, np.maximum(0.0, capital - cfg.withdrawal_floor)),
            0.0,
        )
        bid = np.clip(stale_quote - cfg.spread / 2.0, 0.0, 1.0)
        ask = np.clip(stale_quote + cfg.spread / 2.0, 0.0, 1.0)
        buy_yes = next_fair > ask
        sell_yes = next_fair < bid
        sell_capacity = np.maximum(0.0, cfg.inventory_limit + inventory_yes)
        buy_capacity = np.maximum(0.0, cfg.inventory_limit - inventory_yes)
        trade_depth = np.where(
            buy_yes,
            np.minimum(quoted_depth, sell_capacity),
            np.minimum(quoted_depth, buy_capacity),
        )
        traded = (buy_yes | sell_yes) & (trade_depth > 0.0)
        loss_per_unit = np.where(
            buy_yes,
            np.maximum(0.0, next_fair - ask),
            np.maximum(0.0, bid - next_fair),
        )
        period_loss = trade_depth * loss_per_unit * traded
        period_notional = trade_depth * np.where(buy_yes, ask, bid) * traded
        period_fees = cfg.fee_rate * period_notional
        capital += period_fees - period_loss
        inventory_yes += np.where(
            buy_yes & traded,
            -trade_depth,
            np.where(sell_yes & traded, trade_depth, 0.0),
        )
        adverse_loss += period_loss
        fees += period_fees
        active_depth_periods += quoted_depth

        # Buying a favorable persistence quote is an external cost after
        # consolidation: self-trading would be a wash, while inducing outside
        # holders to sell at the supported quote transfers value out.
        support_budget = np.where(
            active,
            np.minimum(cfg.manipulation_rate * liability, 0.25 * np.maximum(capital, 0.0)),
            0.0,
        )
        quote_bias = cfg.manipulation_impact * support_budget / np.maximum(capital, 1e-9)
        supported_quote = np.clip(next_fair + quote_bias, 0.0, 1.0)
        new_face = cfg.issuance_sensitivity * np.maximum(0.0, supported_quote - next_fair)
        new_proceeds = new_face * supported_quote
        reserve_addition = cfg.reserve_share_of_new_issuance * new_proceeds
        capital_addition = (1.0 - cfg.reserve_share_of_new_issuance) * new_proceeds
        capital += capital_addition - support_budget
        reserve_units += reserve_addition / np.maximum(token_value, 1e-9)
        liability += new_face
        manipulation_spend += support_budget
        issuance_gained += new_face

        failed_oracle = rng.random(n) < cfg.oracle_failure_probability
        period_oracle_loss = cfg.oracle_loss_fraction * capital * failed_oracle
        capital -= period_oracle_loss
        oracle_loss += period_oracle_loss

        if collateral_mode == "native":
            shock_load = np.abs(logit_move) + stressed * cfg.stress_logit_jump
            impairment = np.maximum(0.0, capital_before - capital)
            token_value *= np.exp(
                -cfg.token_stress_beta * shock_load
                - cfg.token_health_beta * impairment / max(cfg.initial_capital, 1e-9)
            )
            token_value = np.clip(token_value, 1e-6, 1.0)

        active &= capital > cfg.withdrawal_floor
        capital = np.maximum(capital, 0.0)
        fair = next_fair
        stale_quote = supported_quote

    terminal_outcome = (rng.random(n) < fair).astype(float)
    settlement_pnl = inventory_yes * (terminal_outcome - fair)
    capital += settlement_pnl
    active &= capital > cfg.withdrawal_floor
    capital = np.maximum(capital, 0.0)
    reserve_value = reserve_units * token_value
    assets = capital + reserve_value
    recovery = np.minimum(1.0, assets / np.maximum(liability, 1e-9))
    mean_depth = active_depth_periods / cfg.periods
    result = {
        "mode": collateral_mode,
        "config": asdict(cfg),
        "ruin_probability": float(np.mean(~active)),
        "mean_recovery": float(np.mean(recovery)),
        "recovery_p10": float(np.quantile(recovery, 0.10)),
        "full_recovery_probability": float(np.mean(recovery >= 1.0 - 1e-12)),
        "mean_final_capital": float(np.mean(capital)),
        "mean_reserve_value": float(np.mean(reserve_value)),
        "mean_token_value": float(np.mean(token_value)),
        "mean_liability": float(np.mean(liability)),
        "mean_depth": float(np.mean(mean_depth)),
        "mean_adverse_selection_loss": float(np.mean(adverse_loss)),
        "mean_inventory_pnl": float(np.mean(inventory_pnl)),
        "mean_settlement_pnl": float(np.mean(settlement_pnl)),
        "mean_abs_final_inventory": float(np.mean(np.abs(inventory_yes))),
        "mean_fees": float(np.mean(fees)),
        "mean_manipulation_spend": float(np.mean(manipulation_spend)),
        "mean_issuance_gained": float(np.mean(issuance_gained)),
        "mean_oracle_loss": float(np.mean(oracle_loss)),
    }
    result["fee_coverage_ratio"] = result["mean_fees"] / max(
        result["mean_adverse_selection_loss"], 1e-12
    )
    result["manipulation_cost_per_face"] = result["mean_manipulation_spend"] / max(
        result["mean_issuance_gained"], 1e-12
    )
    return result


def compare_collateral(config: ConsolConfig | None = None) -> dict:
    """Compare collateral modes on common random draws."""

    cfg = config or ConsolConfig()
    external = simulate_liquidity_consol("external", cfg)
    native = simulate_liquidity_consol("native", cfg)
    return {
        "external": external,
        "native": native,
        "native_minus_external": {
            "mean_recovery": native["mean_recovery"] - external["mean_recovery"],
            "recovery_p10": native["recovery_p10"] - external["recovery_p10"],
            "full_recovery_probability": (
                native["full_recovery_probability"] - external["full_recovery_probability"]
            ),
            "mean_reserve_value": native["mean_reserve_value"] - external["mean_reserve_value"],
        },
    }


def screening_sweep(config: ConsolConfig | None = None) -> list[dict]:
    """Small common-seed sweep over the assumptions most able to save the idea."""

    base = config or ConsolConfig(paths=1_000)
    rows = []
    for fee_rate in (0.01, 0.05, 0.10):
        for spread in (0.02, 0.04, 0.08):
            for manipulation_rate in (0.0, 0.003, 0.012):
                cfg = replace(
                    base,
                    fee_rate=fee_rate,
                    spread=spread,
                    manipulation_rate=manipulation_rate,
                )
                for mode in ("external", "native"):
                    result = simulate_liquidity_consol(mode, cfg)
                    rows.append(
                        {
                            "mode": mode,
                            "fee_rate": fee_rate,
                            "spread": spread,
                            "manipulation_rate": manipulation_rate,
                            "ruin_probability": result["ruin_probability"],
                            "mean_recovery": result["mean_recovery"],
                            "recovery_p10": result["recovery_p10"],
                            "fee_coverage_ratio": result["fee_coverage_ratio"],
                            "mean_depth": result["mean_depth"],
                            "manipulation_cost_per_face": result[
                                "manipulation_cost_per_face"
                            ],
                        }
                    )
    return rows
