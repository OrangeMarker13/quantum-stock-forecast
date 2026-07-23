"""Persistent, horizon-aware feedback for equity forecasts.

Forecasts are only settled after their requested horizon.  This is important:
settling a 30-day prediction with today's close leaks the answer into the
learning signal and makes the apparent accuracy meaningless.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

import numpy as np


MEMORY_FILE = Path(__file__).with_name("prediction_memory.json")
YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
REQUEST_TIMEOUT = 15
MIN_LOCAL_SAMPLES = 3


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _load() -> list[dict[str, Any]]:
    """Load only well-formed memory records; a corrupt file never crashes UI."""
    try:
        with Path(MEMORY_FILE).open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        return [item for item in data if isinstance(item, dict)] if isinstance(data, list) else []
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return []


def _save(data: list[dict[str, Any]]) -> None:
    """Atomically persist memory so an interrupted learner cannot truncate it."""
    memory_path = Path(MEMORY_FILE)
    memory_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{memory_path.name}.", suffix=".tmp", dir=memory_path.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, sort_keys=True, allow_nan=False)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, memory_path)
    except (OSError, TypeError, ValueError):
        try:
            os.unlink(temporary_name)
        except OSError:
            pass
        raise


def _business_day_after(start: date, days: int) -> date:
    """Return the date after *days* trading weekdays (holidays settle next close)."""
    remaining = max(0, int(days))
    current = start
    while remaining:
        current += timedelta(days=1)
        if current.weekday() < 5:
            remaining -= 1
    return current


def _parse_record_date(value: Any) -> date | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def _target_date(prediction: dict[str, Any]) -> date | None:
    target = _parse_record_date(prediction.get("target_date"))
    if target is not None:
        return target
    created = _parse_record_date(prediction.get("created_at") or prediction.get("date"))
    if created is None:
        return None
    try:
        return _business_day_after(created, int(prediction.get("days", 0)))
    except (TypeError, ValueError):
        return None


def _next_id(memory: list[dict[str, Any]]) -> int:
    identifiers = []
    for record in memory:
        try:
            identifiers.append(int(record.get("id", 0)))
        except (TypeError, ValueError):
            continue
    return max(identifiers, default=0) + 1


def store_prediction(
    ticker: str,
    days: int,
    starting_price: float,
    predicted_price: float,
    created_at: datetime | None = None,
) -> int:
    """Store one forecast with an explicit settlement date.

    ``created_at`` is optional and exists mainly for deterministic backtests.
    The application continues to use the original four-argument API.
    """
    cleaned_ticker = str(ticker).upper().strip()
    if not re.fullmatch(r"[A-Z0-9.\-^=]{1,20}", cleaned_ticker):
        raise ValueError("ticker contains unsupported characters")
    horizon = int(days)
    if horizon < 1:
        raise ValueError("forecast horizon must be at least one business day")
    initial = float(starting_price)
    forecast = float(predicted_price)
    if not (np.isfinite(initial) and np.isfinite(forecast) and initial > 0 and forecast > 0):
        raise ValueError("prices must be finite positive numbers")

    created = created_at or _utc_now()
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    created = created.astimezone(timezone.utc)
    memory = _load()
    prediction = {
        "id": _next_id(memory),
        "ticker": cleaned_ticker,
        "days": horizon,
        "created_at": created.isoformat(),
        # Retained for compatibility with existing memory files and reports.
        "date": created.isoformat(),
        "target_date": _business_day_after(created.date(), horizon).isoformat(),
        "starting_price": initial,
        "predicted_price": forecast,
        "actual_price": None,
        "actual_date": None,
        "error_percent": None,
        "completed": False,
        "settlement_status": "pending",
    }
    memory.append(prediction)
    _save(memory)
    return prediction["id"]


def _fetch_close_on_or_after(ticker: str, target: date) -> tuple[float, date] | None:
    """Get the first daily close at or after the target date from Yahoo Finance."""
    start = datetime.combine(target, datetime.min.time(), tzinfo=timezone.utc)
    end = _utc_now() + timedelta(days=1)
    if start >= end:
        return None
    url = YAHOO_CHART_URL.format(ticker=quote(ticker, safe=""))
    try:
        parameters = urlencode({"period1": int(start.timestamp()), "period2": int(end.timestamp()), "interval": "1d"})
        request = Request(f"{url}?{parameters}", headers={"User-Agent": "quantum-stock-forecast/1.0"})
        with urlopen(request, timeout=REQUEST_TIMEOUT) as response:
            result = json.load(response).get("chart", {}).get("result") or []
        if not result:
            return None
        timestamps = result[0].get("timestamp") or []
        quotes = (result[0].get("indicators", {}).get("quote") or [{}])[0]
        closes = quotes.get("close") or []
        for timestamp, close in zip(timestamps, closes):
            if close is None:
                continue
            close_date = datetime.fromtimestamp(timestamp, tz=timezone.utc).date()
            value = float(close)
            if close_date >= target and np.isfinite(value) and value > 0:
                return value, close_date
    except (HTTPError, URLError, OSError, json.JSONDecodeError, ValueError, TypeError, KeyError):
        return None
    return None


def complete_prediction(
    prediction_id: int,
    close_fetcher: Callable[[str, date], tuple[float, date] | None] | None = None,
) -> bool:
    """Settle a due prediction; return ``False`` for not-yet-due or unavailable data."""
    memory = _load()
    for prediction in memory:
        if prediction.get("id") != prediction_id or prediction.get("completed"):
            continue
        target = _target_date(prediction)
        if target is None:
            prediction["settlement_status"] = "invalid_target_date"
            _save(memory)
            return False
        prediction.setdefault("target_date", target.isoformat())
        if _utc_now().date() < target:
            prediction["settlement_status"] = "pending"
            _save(memory)
            return False

        settled = (close_fetcher or _fetch_close_on_or_after)(prediction["ticker"], target)
        if settled is None:
            prediction["settlement_status"] = "awaiting_market_close"
            prediction["last_settlement_attempt"] = _utc_now().isoformat()
            _save(memory)
            return False
        actual_price, actual_date = settled
        predicted_price = float(prediction["predicted_price"])
        if not (np.isfinite(actual_price) and actual_price > 0 and predicted_price > 0):
            prediction["settlement_status"] = "invalid_market_data"
            _save(memory)
            return False

        prediction["actual_price"] = float(actual_price)
        prediction["actual_date"] = actual_date.isoformat()
        # Positive means the model under-predicted and future forecasts need lifting.
        prediction["error_percent"] = (float(actual_price) - predicted_price) / predicted_price
        prediction["completed"] = True
        prediction["settlement_status"] = "completed"
        prediction["completed_at"] = _utc_now().isoformat()
        _save(memory)
        return True
    return False


def settle_due_predictions() -> dict[str, int]:
    """Autonomously settle every due record and report the outcome counts."""
    history = _load()
    result = {"checked": 0, "settled": 0, "pending": 0, "unavailable": 0}
    for prediction in history:
        if prediction.get("completed"):
            continue
        target = _target_date(prediction)
        if target is None or _utc_now().date() < target:
            result["pending"] += 1
            continue
        result["checked"] += 1
        if complete_prediction(prediction.get("id")):
            result["settled"] += 1
        else:
            result["unavailable"] += 1
    return result


def evaluate_predictions() -> list[dict[str, Any]]:
    return _load()


def get_prediction_adjustment_advanced(completed: list[dict[str, Any]], decay: float = 0.15) -> float:
    """Recency-weighted signed forecast bias, bounded against runaway feedback."""
    if not completed:
        return 0.0
    decay = float(np.clip(decay, 0.0, 0.95))
    normalized = []
    for prediction in completed:
        try:
            error = prediction.get("error_percent")
            if error is None:
                error = (float(prediction["actual_price"]) - float(prediction["predicted_price"])) / float(prediction["predicted_price"])
            error = float(error)
            if np.isfinite(error):
                normalized.append((prediction, error))
        except (KeyError, TypeError, ValueError, ZeroDivisionError):
            continue
    if not normalized:
        return 0.0
    normalized.sort(key=lambda item: item[0].get("completed_at") or item[0].get("date") or "")
    weighted_error, weight_total = 0.0, 0.0
    for index, (_, error) in enumerate(normalized):
        weight = (1.0 - decay) ** (len(normalized) - 1 - index)
        weighted_error += error * weight
        weight_total += weight
    adjustment = weighted_error / weight_total if weight_total else 0.0
    return round(float(np.clip(adjustment, -0.05, 0.05)), 6)


def get_prediction_adjustment(ticker: str | None = None, days: int | None = None) -> float:
    """Use the most specific history with enough samples to avoid overfitting."""
    completed = [prediction for prediction in _load() if prediction.get("completed")]
    if not completed:
        return 0.0
    clean_ticker = ticker.upper().strip() if ticker else None
    candidates: list[list[dict[str, Any]]] = []
    if clean_ticker and days is not None:
        candidates.append([p for p in completed if p.get("ticker") == clean_ticker and p.get("days") == days])
    if clean_ticker:
        candidates.append([p for p in completed if p.get("ticker") == clean_ticker])
    if days is not None:
        candidates.append([p for p in completed if p.get("days") == days])
    candidates.append(completed)
    for history in candidates:
        if len(history) >= MIN_LOCAL_SAMPLES:
            return get_prediction_adjustment_advanced(history)
    return 0.0
