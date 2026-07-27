"""Create and settle market forecasts without requiring the Streamlit app."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

import pandas as pd

from prediction_memory import _business_day_after, prediction_exists, settle_due_predictions, store_prediction
from quantum_joint_engine import quantum_joint_forecast
from stock_universe import get_universe, max_tickers


EASTERN = ZoneInfo("America/New_York")
LONG_HORIZONS = (7, 30, 60, 90)
MAX_FAILURES = 15


def _market_now() -> datetime:
    return datetime.now(EASTERN)


def _in_market_window(mode: str, now: datetime | None = None) -> bool:
    now = now or _market_now()
    if now.weekday() >= 5:
        return False
    minute = now.hour * 60 + now.minute
    if mode == "open":
        return 9 * 60 + 45 <= minute <= 10 * 60 + 30
    return 16 * 60 + 5 <= minute <= 17 * 60 + 30


def _seed(*parts: object) -> int:
    value = "|".join(map(str, parts)).encode("utf-8")
    return int.from_bytes(hashlib.sha256(value).digest()[:4], "big")


def _chart(ticker: str, period: str = "2y") -> dict | None:
    params = urlencode({"range": period, "interval": "1d"})
    request = Request(
        f"https://query1.finance.yahoo.com/v8/finance/chart/{quote(ticker, safe='')}?{params}",
        headers={"User-Agent": "market-outlook-forecast/1.0"},
    )
    try:
        with urlopen(request, timeout=15) as response:
            payload = json.load(response)
        result = payload.get("chart", {}).get("result") or []
        return result[0] if result else None
    except (OSError, ValueError, KeyError):
        return None


def _market_inputs(ticker: str, today) -> tuple[pd.DataFrame, float] | None:
    chart = _chart(ticker)
    if chart is None:
        return None
    timestamps = chart.get("timestamp") or []
    quote_data = (chart.get("indicators", {}).get("quote") or [{}])[0]
    frame = pd.DataFrame({"Date": pd.to_datetime(timestamps, unit="s", utc=True), "Close": quote_data.get("close") or []})
    if frame.empty:
        return None
    frame["Date"] = frame["Date"].dt.tz_convert(EASTERN).dt.tz_localize(None)
    frame["Close"] = pd.to_numeric(frame["Close"], errors="coerce")
    frame = frame.dropna().drop_duplicates("Date").sort_values("Date").reset_index(drop=True)
    if len(frame) < 60:
        return None
    metadata = chart.get("meta", {})
    try:
        current_price = float(metadata.get("regularMarketPrice") or frame["Close"].iloc[-1])
    except (TypeError, ValueError):
        return None
    market_time = metadata.get("regularMarketTime")
    if current_price <= 0 or not market_time:
        return None
    quote_date = datetime.fromtimestamp(market_time, tz=timezone.utc).astimezone(EASTERN).date()
    # Prevent a holiday or stale quote from being stored as a same-day forecast.
    if quote_date != today:
        return None
    return frame, current_price


def _forecast_and_store(ticker: str, frame: pd.DataFrame, price: float, horizon: int, target, prediction_type: str) -> bool:
    if prediction_exists(ticker, horizon, target, prediction_type):
        return False
    forecast = quantum_joint_forecast(frame, price, days=horizon, shots=500, seed=_seed(ticker, horizon, target))
    store_prediction(ticker, horizon, price, forecast["expected_price"], target_date=target, prediction_type=prediction_type)
    return True


def run_open_cycle(force: bool = False) -> dict[str, int | str]:
    if not force and not _in_market_window("open"):
        return {"status": "outside_open_window", "created": 0, "failed": 0, "skipped": 0}
    today = _market_now().date()
    outcome: dict[str, int | str] = {"status": "ok", "created": 0, "failed": 0, "skipped": 0}
    for ticker in get_universe()[:max_tickers()]:
        inputs = _market_inputs(ticker, today)
        if inputs is None:
            outcome["failed"] += 1
        else:
            frame, price = inputs
            try:
                plans = [(1, today, "intraday_close")] + [
                    (horizon, _business_day_after(today, horizon), "horizon") for horizon in LONG_HORIZONS
                ]
                for horizon, target, prediction_type in plans:
                    if _forecast_and_store(ticker, frame, price, horizon, target, prediction_type):
                        outcome["created"] += 1
                    else:
                        outcome["skipped"] += 1
            except Exception as error:
                print(f"Forecast skipped for {ticker}: {error}")
                outcome["failed"] += 1
        if outcome["failed"] >= MAX_FAILURES:
            outcome["status"] = "stopped_after_failures"
            break
    return outcome


def run_close_cycle(force: bool = False) -> dict[str, int | str]:
    if not force and not _in_market_window("close"):
        return {"status": "outside_close_window", "settled": 0}
    outcome: dict[str, int | str] = {"status": "ok"}
    outcome.update(settle_due_predictions())
    return outcome


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the unattended market forecaster.")
    parser.add_argument("--mode", choices=("open", "close"), required=True)
    parser.add_argument("--force", action="store_true", help="allow a local/manual run outside market hours")
    args = parser.parse_args()
    result = run_open_cycle(args.force) if args.mode == "open" else run_close_cycle(args.force)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
