"""Small reproducible calibration probe over public Polymarket history.

This is a screening exercise, not a venue-wide study.  It samples closed,
multi-day binary markets from deterministic Gamma API pages, keeps one market
per event to reduce obvious dependence, and reads historical YES prices from
the public CLOB endpoint.  The output records exclusions and missing coverage
so that a small sample cannot silently become evidence for calibration.
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import time
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


GAMMA_MARKETS = "https://gamma-api.polymarket.com/markets"
GAMMA_MARKETS_KEYSET = "https://gamma-api.polymarket.com/markets/keyset"
CLOB_HISTORY = "https://clob.polymarket.com/prices-history"
USER_AGENT = "Mozilla/5.0 fire-liquidity-consol-research/0.1"
HORIZONS_DAYS = (30, 7, 1)
CREDIT_TERMS = (
    "default",
    "bankrupt",
    "insolven",
    "recovery",
    "repay",
    "debt",
    "bond",
    "payment processor",
    "payment corridor",
)


def _request_json(url: str, *, retries: int = 3) -> object:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    error: Exception | None = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.load(response)
        except Exception as exc:  # pragma: no cover - exercised against live API
            error = exc
            if attempt + 1 < retries:
                time.sleep(0.4 * (2**attempt))
    assert error is not None
    raise error


def _parse_json_field(value: object) -> list:
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        parsed = json.loads(value)
        return parsed if isinstance(parsed, list) else []
    return []


def _timestamp(value: str | None) -> int | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return int(parsed.timestamp())
    except (TypeError, ValueError):
        return None


def _market_event_id(market: dict) -> str:
    events = market.get("events") or []
    if events and isinstance(events[0], dict):
        return str(events[0].get("id") or market.get("id"))
    return str(market.get("id"))


def _eligible(market: dict) -> bool:
    outcomes = _parse_json_field(market.get("outcomes"))
    prices = _parse_json_field(market.get("outcomePrices"))
    tokens = _parse_json_field(market.get("clobTokenIds"))
    start = _timestamp(market.get("startDate"))
    close = _timestamp(market.get("closedTime")) or _timestamp(market.get("endDate"))
    if len(outcomes) != 2 or len(prices) != 2 or len(tokens) != 2:
        return False
    if start is None or close is None or close - start < 7 * 86_400:
        return False
    if start < _timestamp("2022-11-18T00:00:00Z"):
        return False
    try:
        terminal = [float(x) for x in prices]
        volume = float(market.get("volumeNum") or market.get("volume") or 0.0)
    except (TypeError, ValueError):
        return False
    return terminal in ([1.0, 0.0], [0.0, 1.0]) and volume >= 1_000.0


def collect_candidates(
    *,
    page_size: int = 100,
    sample_size: int = 60,
    max_pages: int = 100,
) -> tuple[list[dict], dict]:
    """Collect deterministic pages and retain one high-volume market per event."""

    all_rows: list[dict] = []
    pages = 0
    cursor: str | None = None
    for _ in range(max_pages):
        params = {
            "closed": "true",
            "limit": page_size,
            "order": "id",
            "ascending": "false",
        }
        if cursor:
            params["after_cursor"] = cursor
        payload = _request_json(
            f"{GAMMA_MARKETS_KEYSET}?{urllib.parse.urlencode(params)}"
        )
        if not isinstance(payload, dict) or not isinstance(payload.get("markets"), list):
            raise RuntimeError(f"unexpected Gamma keyset response: {payload!r}")
        all_rows.extend(payload["markets"])
        pages += 1
        eligible_now = [market for market in all_rows if _eligible(market)]
        events_now = {_market_event_id(market) for market in eligible_now}
        cursor = payload.get("next_cursor")
        if len(events_now) >= sample_size or not cursor:
            break

    eligible = [market for market in all_rows if _eligible(market)]
    eligible.sort(
        key=lambda market: float(market.get("volumeNum") or market.get("volume") or 0.0),
        reverse=True,
    )
    by_event: dict[str, dict] = {}
    for market in eligible:
        by_event.setdefault(_market_event_id(market), market)
    selected = list(by_event.values())[:sample_size]
    metadata = {
        "pages": pages,
        "markets_seen": len(all_rows),
        "eligible_before_event_deduplication": len(eligible),
        "events_after_deduplication": len(by_event),
        "selected": len(selected),
    }
    return selected, metadata


def _history(token_id: str) -> list[dict]:
    query = urllib.parse.urlencode({"market": token_id, "interval": "max"})
    payload = _request_json(f"{CLOB_HISTORY}?{query}")
    if not isinstance(payload, dict):
        return []
    rows = payload.get("history") or []
    return sorted(
        (
            {"t": int(row["t"]), "p": float(row["p"])}
            for row in rows
            if isinstance(row, dict) and "t" in row and "p" in row
        ),
        key=lambda row: row["t"],
    )


def _snapshot(history: list[dict], target: int, horizon_days: int) -> dict | None:
    prior = [row for row in history if row["t"] <= target]
    if not prior:
        return None
    row = prior[-1]
    tolerance_days = max(2.0, horizon_days * 0.5)
    age_days = (target - row["t"]) / 86_400
    if age_days > tolerance_days:
        return None
    return {"price": row["p"], "timestamp": row["t"], "staleness_days": age_days}


def build_observations(markets: list[dict]) -> tuple[list[dict], dict]:
    observations: list[dict] = []
    histories_with_rows = 0
    history_points: list[int] = []
    credit_adjacent = 0
    event_dates: dict[str, set[str]] = {}
    for market in markets:
        outcomes = _parse_json_field(market["outcomes"])
        terminal = [float(x) for x in _parse_json_field(market["outcomePrices"])]
        tokens = _parse_json_field(market["clobTokenIds"])
        yes_index = next(
            (i for i, outcome in enumerate(outcomes) if str(outcome).lower() == "yes"),
            0,
        )
        close = _timestamp(market.get("closedTime")) or _timestamp(market.get("endDate"))
        start = _timestamp(market.get("startDate"))
        assert close is not None and start is not None
        history = _history(str(tokens[yes_index]))
        histories_with_rows += bool(history)
        history_points.append(len(history))
        question = str(market.get("question") or "")
        is_credit = any(term in question.lower() for term in CREDIT_TERMS)
        credit_adjacent += is_credit
        event_id = _market_event_id(market)
        events = market.get("events") or []
        event = events[0] if events and isinstance(events[0], dict) else {}
        series_rows = event.get("series") or []
        series = (
            str(series_rows[0].get("title") or series_rows[0].get("slug") or "")
            if series_rows and isinstance(series_rows[0], dict)
            else ""
        )
        event_dates.setdefault(event_id, set()).add(str(market.get("endDate") or ""))
        snapshots = {}
        for days in HORIZONS_DAYS:
            snap = _snapshot(history, close - days * 86_400, days)
            if snap is not None:
                snapshots[str(days)] = snap
        observations.append(
            {
                "market_id": str(market.get("id")),
                "event_id": event_id,
                "question": question,
                "category": str(market.get("category") or ""),
                "series": series,
                "start_time": start,
                "close_time": close,
                "duration_days": (close - start) / 86_400,
                "volume": float(market.get("volumeNum") or market.get("volume") or 0.0),
                "outcome": terminal[yes_index],
                "history_points": len(history),
                "credit_adjacent_keyword": is_credit,
                "snapshots": snapshots,
            }
        )
    multi_date_groups = sum(len(dates) >= 2 for dates in event_dates.values())
    coverage = {
        "markets_with_history": histories_with_rows,
        "history_coverage_rate": histories_with_rows / max(len(markets), 1),
        "median_history_points": statistics.median(history_points) if history_points else 0,
        "credit_adjacent_keyword_markets": credit_adjacent,
        "explicit_multi_maturity_event_groups": multi_date_groups,
    }
    return observations, coverage


def _calibration(rows: list[tuple[float, float]]) -> dict:
    if not rows:
        return {"n": 0}
    prices = [row[0] for row in rows]
    outcomes = [row[1] for row in rows]
    brier = statistics.fmean((p - y) ** 2 for p, y in rows)
    bins = []
    calibration_gap = 0.0
    for index in range(5):
        lower = index / 5
        upper = (index + 1) / 5
        members = [
            (p, y)
            for p, y in rows
            if lower <= p < upper or (math.isclose(upper, 1.0) and math.isclose(p, 1.0))
        ]
        if not members:
            continue
        mean_price = statistics.fmean(p for p, _ in members)
        realised = statistics.fmean(y for _, y in members)
        weight = len(members) / len(rows)
        calibration_gap += weight * abs(mean_price - realised)
        bins.append(
            {
                "lower": lower,
                "upper": upper,
                "n": len(members),
                "mean_price": mean_price,
                "realised_frequency": realised,
            }
        )
    return {
        "n": len(rows),
        "mean_price": statistics.fmean(prices),
        "realised_frequency": statistics.fmean(outcomes),
        "brier": brier,
        "expected_calibration_error": calibration_gap,
        "bins": bins,
    }


def summarize(observations: list[dict], collection: dict, coverage: dict) -> dict:
    by_horizon = {}
    for days in HORIZONS_DAYS:
        rows = [
            (float(row["snapshots"][str(days)]["price"]), float(row["outcome"]))
            for row in observations
            if str(days) in row["snapshots"]
        ]
        by_horizon[str(days)] = _calibration(rows)

    volume_values = [row["volume"] for row in observations]
    volume_median = statistics.median(volume_values) if volume_values else 0.0
    seven_day = [
        row for row in observations if "7" in row["snapshots"]
    ]
    low_volume = _calibration(
        [
            (row["snapshots"]["7"]["price"], row["outcome"])
            for row in seven_day
            if row["volume"] < volume_median
        ]
    )
    high_volume = _calibration(
        [
            (row["snapshots"]["7"]["price"], row["outcome"])
            for row in seven_day
            if row["volume"] >= volume_median
        ]
    )
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": {
            "markets": GAMMA_MARKETS,
            "history": CLOB_HISTORY,
            "sample_rule": (
                "closed binary markets, duration >=7 days, volume >=1000, "
                "one highest-volume market per event, descending-id Gamma keyset pages"
            ),
        },
        "collection": collection,
        "coverage": coverage,
        "sample_concentration": {
            "categories": dict(Counter(row["category"] or "(missing)" for row in observations)),
            "series": dict(Counter(row["series"] or "(missing)" for row in observations)),
        },
        "calibration_by_days_before_close": by_horizon,
        "seven_day_volume_split": {
            "median_market_volume": volume_median,
            "below_median": low_volume,
            "at_or_above_median": high_volume,
        },
        "limits": {
            "credit_specific_inference": (
                "unsupported unless credit_adjacent_keyword_markets is materially nonzero"
            ),
            "fractional_recovery": "not measured by binary settlement outcomes",
            "liquidity_persistence": (
                "not identified by sparse price history; requires historical order-book depth"
            ),
            "term_structure": (
                "not identified unless explicit_multi_maturity_event_groups is nonzero"
            ),
            "dependence": (
                "one market per event removes obvious duplicates but does not remove shared shocks"
            ),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample-size", type=int, default=60)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "data" / "polymarket_probe.json",
    )
    args = parser.parse_args()
    markets, collection = collect_candidates(sample_size=args.sample_size)
    observations, coverage = build_observations(markets)
    payload = {
        "summary": summarize(observations, collection, coverage),
        "observations": observations,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload["summary"], indent=2))
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
