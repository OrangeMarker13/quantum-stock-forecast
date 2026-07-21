import os
import uuid
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
    "Market_Regime",
    "Volatility",
    "Model_Version",
    "Completed"
]


# ============================================================
# INITIALIZATION
# ============================================================

def initialize_memory():

    if not os.path.exists(MEMORY_FILE):

        pd.DataFrame(
            columns=COLUMNS
        ).to_csv(
            MEMORY_FILE,
            index=False
        )



# ============================================================
# LOAD MEMORY
# ============================================================

def load_memory():

    initialize_memory()

    try:

        data = pd.read_csv(
            MEMORY_FILE
        )

        return data

    except Exception:

        return pd.DataFrame(
            columns=COLUMNS
        )



# ============================================================
# SAVE NEW PREDICTION
# ============================================================

def save_prediction(
    ticker,
    predicted_price,
    horizon,
    confidence,
    regime,
    volatility,
    model_version="v1"
):

    history = load_memory()


    prediction = {

        "ID":
        str(uuid.uuid4()),

        "Ticker":
        ticker.upper(),

        "Created_Time":
        datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),

        "Forecast_Horizon":
        horizon,

        "Predicted_Price":
        float(predicted_price),

        "Actual_Price":
        np.nan,

        "Residual":
        np.nan,

        "Residual_Percent":
        np.nan,

        "Absolute_Error_Percent":
        np.nan,

        "Confidence":
        float(confidence),

        "Market_Regime":
        regime,

        "Volatility":
        float(volatility),

        "Model_Version":
        model_version,

        "Completed":
        False

    }


    history = pd.concat(
        [
            history,
            pd.DataFrame([prediction])
        ],
        ignore_index=True
    )


    history.to_csv(
        MEMORY_FILE,
        index=False
    )


    return prediction["ID"]



# ============================================================
# UPDATE PREDICTION AFTER REAL PRICE
# ============================================================

def complete_prediction(
    prediction_id,
    actual_price
):

    history = load_memory()


    matches = history.index[
        history["ID"] == prediction_id
    ]


    if len(matches) == 0:

        return False


    index = matches[0]


    predicted = float(
        history.loc[
            index,
            "Predicted_Price"
        ]
    )


    actual = float(
        actual_price
    )


    residual = (
        actual -
        predicted
    )


    residual_percent = (
        residual /
        predicted
    ) * 100


    absolute_error = abs(
        residual_percent
    )


    history.loc[
        index,
        "Actual_Price"
    ] = actual


    history.loc[
        index,
        "Residual"
    ] = residual


    history.loc[
        index,
        "Residual_Percent"
    ] = residual_percent


    history.loc[
        index,
        "Absolute_Error_Percent"
    ] = absolute_error


    history.loc[
        index,
        "Completed"
    ] = True



    history.to_csv(
        MEMORY_FILE,
        index=False
    )


    return True



# ============================================================
# GET STOCK HISTORY
# ============================================================

def get_stock_history(
    ticker
):

    history = load_memory()


    return history[
        history["Ticker"] ==
        ticker.upper()
    ]



# ============================================================
# MODEL BIAS
# ============================================================

def get_prediction_bias(
    ticker,
    horizon=None
):

    data = get_stock_history(
        ticker
    )


    data = data[
        data["Completed"] == True
    ]


    if horizon:

        data = data[
            data["Forecast_Horizon"] ==
            horizon
        ]


    if data.empty:

        return 0



    recent = data.tail(50)


    return recent[
        "Residual"
    ].mean()



# ============================================================
# ACCURACY METRICS
# ============================================================

def get_model_accuracy(
    ticker,
    horizon=None
):

    data = get_stock_history(
        ticker
    )


    data = data[
        data["Completed"] == True
    ]


    if horizon:

        data = data[
            data["Forecast_Horizon"] ==
            horizon
        ]


    if data.empty:

        return {

            "samples":0,

            "accuracy":0,

            "average_error":0

        }



    error = data[
        "Absolute_Error_Percent"
    ].mean()



    accuracy = max(
        0,
        100 - error
    )



    return {

        "samples":
        len(data),

        "accuracy":
        accuracy,

        "average_error":
        error

    }



# ============================================================
# FACTOR PERFORMANCE SUPPORT
# ============================================================

def get_recent_performance(
    ticker
):

    data = get_stock_history(
        ticker
    )


    data = data[
        data["Completed"] == True
    ]


    if data.empty:

        return None



    return {

        "bias":
        data["Residual"].mean(),

        "accuracy":
        100 -
        data["Absolute_Error_Percent"].mean(),

        "samples":
        len(data)

    }



# ============================================================
# CLEAN OLD DATA
# ============================================================

def clean_memory(
    max_rows=10000
):

    history = load_memory()


    if len(history) > max_rows:

        history = history.tail(
            max_rows
        )


        history.to_csv(
            MEMORY_FILE,
            index=False
        )
