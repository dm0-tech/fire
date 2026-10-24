"""Run the adversarial liquidity-consol comparison and write its summary."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sim.liquidity_consol import compare_collateral, screening_sweep


def main() -> None:
    comparison = compare_collateral()
    sweep = screening_sweep()
    output = {
        "comparison": comparison,
        "sweep": sweep,
        "screening": {
            "criteria": {
                "ruin_probability_max": 0.05,
                "recovery_p10_min": 0.90,
                "fee_coverage_ratio_min": 1.0,
            },
            "passing_rows": sum(
                row["ruin_probability"] <= 0.05
                and row["recovery_p10"] >= 0.90
                and row["fee_coverage_ratio"] >= 1.0
                for row in sweep
            ),
            "total_rows": len(sweep),
        },
    }
    path = Path(__file__).resolve().parent / "out" / "liquidity_consol_summary.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output, indent=2))
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
