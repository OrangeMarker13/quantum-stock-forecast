# ============================================================
# PREDICTION MEMORY ENGINE
# Adaptive Forecast Feedback System
# ============================================================

import json
import os
from datetime import datetime


MEMORY_FILE = "prediction_memory.json"


def _load():
    if not os.path.exists(MEMORY_FILE):
        return []
    try:
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    except:
        return []


def _save(data):
    try:
        with open(MEMORY_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except:
        pass


# ============================================================
# STORE FORECAST
# ============================================================

def store_prediction(
    ticker,
    days,
    starting_price,
    predicted_price
):

    memory = _load()

    prediction = {
        "id": len(memory) + 1,
        "ticker": ticker,
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


# ============================================================
# COMPLETE PREDICTION
# ============================================================

def complete_prediction(
    prediction_id,
    actual_price
):

    memory = _load()

    for p in memory:

        if p["id"] == prediction_id:

            p["actual_price"] = float(actual_price)

            p["error_percent"] = abs(
                actual_price - p["predicted_price"]
            ) / p["predicted_price"] * 100

            p["completed"] = True

            _save(memory)

            return True

    return False


# ============================================================
# GET HISTORY
# ============================================================

def evaluate_predictions():

    return _load()


# ============================================================
# ADAPTIVE MODEL CORRECTION
# ============================================================

def get_prediction_adjustment():

    history = _load()

    errors = []

    for p in history:

        if p.get("completed"):

            errors.append(
                p["actual_price"]
                -
                p["predicted_price"]
            )

    if not errors:
        return 0

    adjustment = sum(errors) / len(errors)

    return round(adjustment, 4)
