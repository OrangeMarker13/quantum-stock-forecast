# ============================================================
# PREDICTION_MEMORY.PY
# Adaptive Forecast Feedback System (EWAB Ticker-Specific Engine)
# ============================================================
import json
import os
from datetime import datetime

MEMORY_FILE = "prediction_memory.json"

def _load():
    if not os.path.exists(MEMORY_FILE): return []
    try:
        with open(MEMORY_FILE, "r") as f: return json.load(f)
    except: return []

def _save(data):
    try:
        with open(MEMORY_FILE, "w") as f: json.dump(data, f, indent=2)
    except: pass

def store_prediction(ticker, days, starting_price, predicted_price):
    memory = _load()
    prediction = {
        "id": len(memory) + 1,
        "ticker": ticker.upper().strip(),
        "days": days,
        "date": datetime.now().isoformat(),
        "starting_price": float(starting_price),
        "predicted_price": float(predicted_price),
        "actual_price": None,
        "error_percent": None,
        "completed": False
    }
    memory.append(prediction)
    _save(memory)
    return prediction["id"]

def complete_prediction(prediction_id):
    memory = _load()

    for p in memory:
        if p["id"] == prediction_id and not p["completed"]:
            try:
                import yfinance as yf
                actual_price = float(
                    yf.Ticker(p["ticker"]).history(period="1d")["Close"].iloc[-1]
                )
            except:
                return False

            p["actual_price"] = actual_price
            p["error_percent"] = abs(actual_price - p["predicted_price"]) / p["predicted_price"] * 100
            p["completed"] = True
            _save(memory)
            return True

    return False

def evaluate_predictions():
    return _load()

def get_prediction_adjustment_advanced(completed, decay=0.15):
    if not completed: return 0.0
    completed.sort(key=lambda x: x.get("id", 0))
    weighted_sum, weight_total = 0.0, 0.0
    for i, p in enumerate(completed):
        error = p["actual_price"] - p["predicted_price"]
        weight = (1.0 - decay) ** (len(completed) - 1 - i)
        weighted_sum += error * weight
        weight_total += weight
    return round(weighted_sum / (weight_total + 1e-9), 4)

def get_prediction_adjustment(ticker=None):
    history = _load()
    completed = [p for p in history if p.get("completed")]
    if ticker:
        ticker = ticker.upper().strip()
        filtered = [p for p in completed if p.get("ticker", "").upper().strip() == ticker]
        if filtered:
            return get_prediction_adjustment_advanced(filtered)
    return get_prediction_adjustment_advanced(completed)
