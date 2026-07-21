import os
import time
import requests
import pandas as pd


DATA_FOLDER = "data"


if not os.path.exists(DATA_FOLDER):

    os.makedirs(DATA_FOLDER)



# ============================================================
# SAVE LOCAL DATA
# ============================================================


def save_stock_data(
    ticker,
    prices
):

    try:

        filepath = (
            f"{DATA_FOLDER}/{ticker}.csv"
        )


        dataframe = pd.DataFrame(
            {
                "Close": prices
            }
        )


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
# LOAD LOCAL DATA
# ============================================================


def load_saved_data(
    ticker
):

    try:

        filepath = (
            f"{DATA_FOLDER}/{ticker}.csv"
        )


        if not os.path.exists(filepath):

            return pd.Series(
                dtype=float
            )



        data = pd.read_csv(
            filepath
        )


        if "Close" not in data.columns:

            return pd.Series(
                dtype=float
            )



        prices = (
            data["Close"]
            .dropna()
            .astype(float)
        )


        return prices



    except Exception as error:

        print(
            "Local data error:",
            error
        )


        return pd.Series(
            dtype=float
        )



# ============================================================
# HISTORICAL MARKET DATA
# ============================================================


def get_stock_data(
    ticker
):


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



        if response.status_code != 200:


            print(

                "Yahoo status:",
                response.status_code

            )


            saved = load_saved_data(
                ticker
            )


            if not saved.empty:

                return saved



            return pd.Series(
                dtype=float
            )



        json_data = response.json()



        result = (

            json_data
            .get("chart", {})
            .get("result")

        )



        if not result:


            print(
                "No Yahoo chart result"
            )


            saved = load_saved_data(
                ticker
            )


            return saved



        quote = (

            result[0]
            ["indicators"]
            ["quote"][0]

        )



        closes = quote.get(
            "close"
        )



        if closes is None:


            print(
                "No close prices"
            )


            saved = load_saved_data(
                ticker
            )


            return saved



        prices = pd.Series(
            closes
        )



        prices = (

            prices
            .dropna()
            .astype(float)

        )



        if len(prices) < 20:


            print(
                "Not enough Yahoo data"
            )


            saved = load_saved_data(
                ticker
            )


            return saved



        save_stock_data(

            ticker,

            prices

        )



        print(

            ticker,

            "historical points:",

            len(prices)

        )



        return prices



    except Exception as error:


        print(

            "Historical data error:",

            error

        )


        saved = load_saved_data(
            ticker
        )


        return saved



# ============================================================
# LIVE PRICE
# ============================================================


def get_live_price(
    ticker
):


    url = (

        f"https://query1.finance.yahoo.com/"
        f"v8/finance/chart/{ticker}"

    )



    try:


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



        return float(
            price
        )



    except Exception as error:


        print(

            "Live price error:",

            error

        )


        return None
