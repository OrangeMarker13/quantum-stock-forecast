import os
import requests
import pandas as pd
import numpy as np


DATA_FOLDER = "data"


if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)



# ============================================================
# SAVE DATA
# ============================================================


def save_stock_data(ticker, dataframe):

    try:

        filepath = f"{DATA_FOLDER}/{ticker}.csv"

        dataframe.to_csv(
            filepath,
            index=False
        )

    except Exception as error:

        print(
            "Save error:",
            error
        )



# ============================================================
# LOAD SAVED DATA
# ============================================================


def load_saved_data(ticker):

    try:

        filepath = f"{DATA_FOLDER}/{ticker}.csv"


        if not os.path.exists(filepath):

            return None



        data = pd.read_csv(
            filepath
        )


        return data



    except Exception as error:

        print(
            "Load error:",
            error
        )


        return None



# ============================================================
# TECHNICAL INDICATORS
# ============================================================


def add_indicators(data):


    data["Return"] = (

        data["Close"]

        .pct_change()

    )



    data["SMA20"] = (

        data["Close"]

        .rolling(20)

        .mean()

    )



    data["SMA50"] = (

        data["Close"]

        .rolling(50)

        .mean()

    )



    delta = data["Close"].diff()



    gain = delta.clip(
        lower=0
    )



    loss = -delta.clip(
        upper=0
    )



    avg_gain = (

        gain

        .rolling(14)

        .mean()

    )



    avg_loss = (

        loss

        .rolling(14)

        .mean()

    )



    rs = avg_gain / avg_loss



    data["RSI"] = (

        100 -

        (

            100 /

            (1 + rs)

        )

    )



    data["Volatility"] = (

        data["Return"]

        .rolling(20)

        .std()

    )



    data["Momentum"] = (

        data["Close"]

        /

        data["Close"]

        .shift(20)

        -

        1

    )



    if "Volume" in data.columns:

        data["Volume_Change"] = (

            data["Volume"]

            .pct_change()

        )



    return data



# ============================================================
# YAHOO HISTORICAL DATA
# ============================================================


def get_stock_data(ticker):


    url = (

        f"https://query1.finance.yahoo.com/"
        f"v8/finance/chart/{ticker}"
        f"?range=2y&interval=1d"

    )



    try:


        response = requests.get(

            url,

            headers={

                "User-Agent":

                "Mozilla/5.0"

            },

            timeout=15

        )



        data = response.json()



        result = (

            data

            .get("chart", {})

            .get("result")

        )



        if not result:

            saved = load_saved_data(ticker)

            return saved



        result = result[0]



        timestamps = result["timestamp"]



        quote = (

            result

            ["indicators"]

            ["quote"][0]

        )



        dataframe = pd.DataFrame(

            {

                "Date":

                pd.to_datetime(

                    timestamps,

                    unit="s"

                ),

                "Close":

                quote["close"],

                "Volume":

                quote["volume"]

            }

        )



        dataframe = (

            dataframe

            .dropna()

        )



        dataframe = add_indicators(
            dataframe
        )



        save_stock_data(

            ticker,

            dataframe

        )



        return dataframe



    except Exception as error:


        print(

            "Market data error:",

            error

        )


        return load_saved_data(
            ticker
        )



# ============================================================
# LIVE PRICE
# ============================================================


def get_live_price(ticker):


    try:


        url = (

            f"https://query1.finance.yahoo.com/"
            f"v8/finance/chart/{ticker}"

        )



        response = requests.get(

            url,

            headers={

                "User-Agent":

                "Mozilla/5.0"

            },

            timeout=10

        )



        data = response.json()



        price = (

            data

            ["chart"]

            ["result"][0]

            ["meta"]

            ["regularMarketPrice"]

        )



        return float(price)



    except Exception:


        return None
