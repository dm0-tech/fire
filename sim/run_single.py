"""Single-issuer experiments. Writes figures to sim/out/."""

from __future__ import annotations

import json
import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from sim.experiments import (
    calibration,
    e1_sovereigns,
    e2_overissue,
    e3_headline,
    e3_ensemble,
    e4_volatility,
    e5_premium,
    e6_manipulation,
    e7_run,
    e8_growth,
    e8_perp,
    regime_ensemble,
)
from sim.forecaster import choose


def _out() -> Path:
    path = ROOT / "sim" / "out"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _save(fig, name: str) -> None:
    fig.tight_layout()
    fig.savefig(_out() / name, dpi=120)
    plt.close(fig)


def main() -> None:
    winner = choose(seed=7)
    from sim.forecaster import choose as chosen

    scores = getattr(chosen, "scores", {})
    summary: dict = {
        "metadata": {
            "python": platform.python_version(),
            "forecast_paths": 128,
            "ensemble_seeds": 20,
        },
        "forecaster": winner,
        "brier_scores": scores,
    }

    vol = e4_volatility()
    summary["E4"] = {
        "sigma2_over_2": vol["sigma2_over_2"],
        "mean_du": vol["mean_du"],
        "mean_d_shortfall": vol["mean_d_shortfall"],
    }
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(np.cumsum(vol["du_path"]), label="mean cumulative Δu")
    ax.plot(np.arange(len(vol["du_path"])) * vol["sigma2_over_2"], label="σ²/2 per step")
    ax.plot(np.cumsum(vol["short_path"]), label="mean cumulative Δ(1−p)")
    ax.set_title("E4  volatility with the physical state held fixed")
    ax.set_xlabel("step")
    ax.legend()
    _save(fig, "E4_volatility.png")

    perp = e8_perp()
    growth = e8_growth()
    summary["E8"] = {
        "B0_still_rising": perp["B0_still_rising"],
        "B1_gap": perp["B1_gap"],
        "B1_closed": perp["B1_closed"],
        "g_M": growth["g_M"],
        "g_Y": growth["g_Y"],
        "mean_kl": growth["mean_kl"],
        "excess": growth["excess"],
        "within_bound": growth["within_bound"],
    }
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(perp["m"], perp["B0"], label="B0")
    ax.plot(perp["m"], perp["B1"], label="B1")
    ax.plot(perp["m"], perp["B2"], label="B2")
    ax.axhline(perp["B1_closed"], color="black", lw=0.8, label="B1 closed form")
    ax.set_title("E8  perp partial sums under constant hazard")
    ax.set_xlabel("truncation horizon")
    ax.legend()
    _save(fig, "E8_perp.png")

    e1 = e1_sovereigns()
    summary["E1"] = {
        "crisis_falling_hazard": e1["crisis_curve"]["falling_hazard"],
        "crisis_inverted_yield": e1["crisis_curve"]["inverted_yield"],
        "healthy_final_S": float(e1["healthy"]["S"][-1]),
        "weak_final_S": float(e1["weak"]["S"][-1]),
        "healthy_yield_slope": e1["healthy"]["yield_slope"],
        "weak_yield_slope": e1["weak"]["yield_slope"],
    }
    fig, axes = plt.subplots(1, 2, figsize=(9, 4))
    for name in ("healthy", "weak"):
        axes[0].plot(e1[name]["S"], label=name)
        axes[1].plot(e1[name]["Y"], label=name)
    axes[0].set_title("E1  structure")
    axes[1].set_title("E1  output")
    axes[0].legend()
    axes[1].legend()
    _save(fig, "E1_sovereigns.png")
    fig, ax = plt.subplots(figsize=(6, 4))
    for name in ("healthy", "weak"):
        for t, snap in e1[name]["snaps"].items():
            ax.plot(snap["lags"], snap["r"], label=f"{name} t={t}")
    ax.set_title("E1  yield curves")
    ax.set_xlabel("maturity lag")
    ax.legend(fontsize=7)
    _save(fig, "E1_yields.png")
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(e1["crisis_curve"]["r"], label="yield, conditional on crisis")
    ax.plot(e1["crisis_curve"]["hazard"], label="forward hazard")
    ax.set_title("E1  crisis term structure")
    ax.legend()
    _save(fig, "E1_crisis.png")

    e2 = e2_overissue()
    summary["E2"] = {
        "first_bind": e2["first_bind"],
        "S_at_bind": e2["S_at_bind"],
        "S_min_after": e2["S_min_after"],
    }
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(e2["aggressive_U"], label="U")
    ax.plot(e2["aggressive_B"], label="ceiling")
    ax.plot(e2["aggressive_S"], label="S")
    ax.set_title("E2  issuance against a low maintenance share")
    ax.legend()
    _save(fig, "E2_overissue.png")

    e5 = e5_premium()
    summary["E5"] = {
        "identity_gap": e5["identity_gap"],
        "theta_where_ceiling_binds": next((r["theta"] for r in e5["rows"] if r["ceiling_binds"]), None),
        "ell_at_zero": e5["rows"][0]["ell"],
        "ell_at_end": e5["rows"][-1]["ell"],
    }
    fig, ax = plt.subplots(figsize=(6, 4))
    theta = [r["theta"] for r in e5["rows"]]
    ax.plot(theta, [r["u_P"] for r in e5["rows"]], label="u^P")
    ax.plot(theta, [r["premium_component"] for r in e5["rows"]], label="log(1+θ)")
    ax.plot(theta, [r["u_Q"] for r in e5["rows"]], label="u^Q")
    ax.plot(theta, [r["ell"] for r in e5["rows"]], label="ℓ(p^Q)")
    ax.set_title("E5  risk premium with the physical state fixed")
    ax.set_xlabel("θ")
    ax.legend()
    _save(fig, "E5_premium.png")

    e6 = e6_manipulation()
    summary["E6"] = e6["rows"]
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot([r["zeta"] for r in e6["rows"]], [r["bias"] for r in e6["rows"]], label="price bias")
    ax.plot([r["zeta"] for r in e6["rows"]], [r["discounted_Y"] for r in e6["rows"]], label="discounted output")
    ax.set_xlabel("ζ")
    ax.set_title("E6  levy, bias, and output")
    ax.legend()
    _save(fig, "E6_manipulation.png")

    e7 = e7_run()
    summary["E7"] = {
        name: {"M_change_after_trigger": row["M_change_after_trigger"], "multiplicity": row["multiplicity"]}
        for name, row in e7.items()
    }
    fig, ax = plt.subplots(figsize=(6, 4))
    for name, row in e7.items():
        ax.plot(row["M"], label=name)
    ax.axvline(15, color="black", lw=0.6)
    ax.set_title("E7  money stock, exit at t=15")
    ax.legend(fontsize=7)
    _save(fig, "E7_run.png")

    e3 = e3_headline()
    summary["E3"] = {
        name: {
            "discounted_Y": row["discounted_Y"],
            "final_S": row["final_S"],
            "mean_abs_gap": row["mean_abs_gap"],
            "issued_face": float(np.sum(row["issued_face"])),
            "retired_money": float(np.sum(row["retired_money"])),
            "multiplicity": row["multiplicity"],
        }
        for name, row in e3["policies"].items()
    }
    summary["E3"]["sweep"] = e3["sweep"]
    summary["E3_ensemble"] = e3_ensemble()
    summary["regime_ensemble"] = regime_ensemble()
    fig, axes = plt.subplots(2, 2, figsize=(9, 7))
    for name, row in e3["policies"].items():
        axes[0, 0].plot(row["P_gap"], label=name)
        axes[0, 1].plot(row["M"], label=name)
        axes[1, 0].plot(row["S"], label=name)
        axes[1, 1].plot(row["Y"], label=name)
    axes[0, 0].set_title("price-level gap")
    axes[0, 1].set_title("money stock")
    axes[1, 0].set_title("structure")
    axes[1, 1].set_title("output")
    axes[0, 0].legend(fontsize=7)
    _save(fig, "E3_headline.png")

    cal = calibration()
    summary["calibration"] = {
        "brier": cal["brier"],
        "mean_wedge": cal["mean_wedge"],
        "centers": cal["centers"],
        "frequencies": cal["frequencies"],
    }
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.plot([0, 1], [0, 1], color="black", lw=0.6)
    ax.plot(cal["centers"], cal["frequencies"], marker="o")
    ax.set_title("Forecaster reliability, physical measure")
    ax.set_xlabel("forecast p^P")
    ax.set_ylabel("realised mean φ")
    _save(fig, "calibration.png")

    def convert(obj):
        if isinstance(obj, dict):
            return {str(k): convert(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [convert(v) for v in obj]
        if isinstance(obj, (np.floating, np.integer)):
            return obj.item()
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return obj

    (_out() / "summary.json").write_text(json.dumps(convert(summary), indent=2, allow_nan=False))
    print(f"forecaster {winner} scores {scores}")
    print(f"wrote {_out()}")


if __name__ == "__main__":
    main()
