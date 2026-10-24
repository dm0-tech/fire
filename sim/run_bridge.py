"""Two-issuer bridge experiment and the single-issuer functional bakeoff.

The bakeoff is single-issuer, but it compares the rules the bridge accounting
also depends on, and the prompt's second entry point has to produce figures
on its own.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sim.experiments import e10_bakeoff, e10_ensemble, e9_bridge


def main() -> None:
    out = ROOT / "sim" / "out"
    out.mkdir(parents=True, exist_ok=True)

    bridge = e9_bridge()
    fig, ax = plt.subplots(figsize=(6, 4))
    share = [r["share"] for r in bridge["rows"]]
    ax.plot(share, [r["price_gap"] for r in bridge["rows"]], marker="o", label="marginal price − joint price")
    ax.plot(share, [r["mutual_information"] for r in bridge["rows"]], marker="o", label="mutual information (nats)")
    ax.plot(share, [r["surprisal_gap"] for r in bridge["rows"]], marker="o", label="surprisal gap")
    ax.set_xlabel("common-shock share")
    ax.set_title("E9  bridge priced from marginals versus the joint")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out / "E9_bridge.png", dpi=120)
    plt.close(fig)

    bake = e10_bakeoff()
    fig, ax = plt.subplots(figsize=(6, 4))
    for rule, scales in bake.items():
        ax.plot([0.5, 1.0, 2.0], [scales[f]["mean_abs_gap"] for f in (0.5, 1.0, 2.0)], marker="o", label=rule)
    ax.set_xlabel("ceiling scale factor")
    ax.set_ylabel("mean absolute price gap")
    ax.set_title("E10  price-level gap by budget rule")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out / "E10_bakeoff.png", dpi=120)
    plt.close(fig)

    def convert(obj):
        if isinstance(obj, dict):
            return {str(k): convert(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [convert(v) for v in obj]
        return obj

    (out / "bridge_summary.json").write_text(
        json.dumps(
            {
                "metadata": {
                    "single_issuer_forecast_paths": 128,
                    "bridge_paths_per_share": 300,
                    "ensemble_seeds": 20,
                },
                "E9": bridge,
                "E10": convert(bake),
                "E10_ensemble": e10_ensemble(),
            },
            indent=2,
            allow_nan=False,
        )
    )
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
