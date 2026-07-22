import os
import uuid
import json
import pandas as pd
import numpy as np
from datetime import datetime


MEMORY_FILE = "prediction_history.csv"

COLUMNS = [
    "ID",
    "Ticker",
    "Created_Time",
    "Forecast_Horizon",
    "Predicted_Price",
    "Actual_Price",
    "Residual",
    "Residual_Percent",
    "Absolute_Error_Percent",
    "Confidence",
    "Quantum_Score",
    "Signal_Weights",
    "Feature_Importance",
    "Market_Regime",
    "Volatility",
    "Model_Version",
    "Completed"
]


def initialize_memory():
    if not os.path.exists(MEMORY_FILE):
        pd.DataFrame(columns=COLUMNS).to_csv(
            MEMORY_FILE,
            index=False
        )


def load_memory():
    initialize_memory()

    try:
        data = pd.read_csv(MEMORY_FILE)

        for col in COLUMNS:
            if col not in data.columns:
                data[col] = np.nan

        return data[COLUMNS]

    except Exception:
        return pd.DataFrame(columns=COLUMNS)


def save_memory(data):
    try:
        data.to_csv(
            MEMORY_FILE,
            index=False
        )
        return True
    except Exception:
        return False


def save_prediction(
    ticker,
    predicted_price,
    horizon,
    confidence,
    regime,
    volatility,
    quantum_score=0,
    signal_weights=None,
    feature_importance=None,
    model_version="v1"
):

    history = load_memory()

    prediction = {
        "ID": str(uuid.uuid4()),
        "Ticker": ticker.upper(),
        "Created_Time": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        "Forecast_Horizon": horizon,
        "Predicted_Price": float(predicted_price),
        "Actual_Price": np.nan,
        "Residual": np.nan,
        "Residual_Percent": np.nan,
        "Absolute_Error_Percent": np.nan,
        "Confidence": float(confidence),
        "Quantum_Score": float(quantum_score),
        "Signal_Weights": json.dumps(signal_weights or {}),
        "Feature_Importance": json.dumps(feature_importance or {}),
        "Market_Regime": regime,
        "Volatility": float(volatility),
        "Model_Version": model_version,
        "Completed": False
    }

    history = pd.concat(
        [
            history,
            pd.DataFrame([prediction])
        ],
        ignore_index=True
    )

    save_memory(history)

    return prediction["ID"]


def complete_prediction(
    prediction_id,
    actual_price
):

    history = load_memory()

    match = history.index[
        history["ID"] == prediction_id
    ]

    if len(match) == 0:
        return False

    i = match[0]

    predicted = float(
        history.loc[i, "Predicted_Price"]
    )

    actual = float(actual_price)

    residual = actual - predicted

    error = (
        residual / predicted * 100
        if predicted
        else 0
    )

    history.loc[i, "Actual_Price"] = actual
    history.loc[i, "Residual"] = residual
    history.loc[i, "Residual_Percent"] = error
    history.loc[i, "Absolute_Error_Percent"] = abs(error)
    history.loc[i, "Completed"] = True

    return save_memory(history)


def get_stock_history(ticker):
    data = load_memory()

    return data[
        data["Ticker"] == ticker.upper()
    ]


def get_prediction_bias(ticker, horizon=None):

    data = get_stock_history(ticker)

    data = data[
        data["Completed"] == True
    ]

    if horizon:
        data = data[
            data["Forecast_Horizon"] == horizon
        ]

    if data.empty:
        return 0

    return data.tail(50)["Residual"].mean()


def get_model_accuracy(ticker, horizon=None):

    data = get_stock_history(ticker)

    data = data[
        data["Completed"] == True
    ]

    if horizon:
        data = data[
            data["Forecast_Horizon"] == horizon
        ]

    if data.empty:
        return {
            "samples":0,
            "accuracy":0,
            "average_error":0
        }

    error = data["Absolute_Error_Percent"].mean()

    return {
        "samples":len(data),
        "accuracy":max(0,100-error),
        "average_error":error
    }


def get_recent_performance(ticker):

    data = get_stock_history(ticker)

    data = data[
        data["Completed"] == True
    ]

    if data.empty:
        return None

    return {
        "bias":data["Residual"].mean(),
        "accuracy":max(
            0,
            100-data["Absolute_Error_Percent"].mean()
        ),
        "samples":len(data)
    }


def clean_memory(max_rows=10000):

    data = load_memory()

    if len(data) > max_rows:
        data = data.tail(max_rows)
        save_memory(data)

    return True


def clear_memory():

    try:
        if os.path.exists(MEMORY_FILE):
            os.remove(MEMORY_FILE)

        initialize_memory()

        return True

    except Exception:
        return False
def evaluate_predictions():
    return load_memory()


def get_prediction_adjustment():

    data = load_memory()

    completed = data[
        data["Completed"] == True
    ]

    if completed.empty:
        return 0

    return completed[
        "Residual_Percent"
    ].mean()
