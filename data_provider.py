import pandas as pd
import requests
import time


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
                "User-Agent": "Mozilla/5.0"
            },
            timeout=10
        )


        data = response.json()


        result = data["chart"]["result"][0]


        timestamps = result["timestamp"]

        closes = result["indicators"]["quote"][0]["close"]


        prices = pd.Series(
            closes
        )


        prices = (
            prices
            .dropna()
            .astype(float)
        )


        return prices


    except Exception as error:

        print(
            "DATA PROVIDER ERROR:",
            error
        )

        return pd.Series(
            dtype=float
        )



def get_live_price(ticker):

    try:

        url = (
            f"https://query1.finance.yahoo.com/"
            f"v8/finance/chart/{ticker}"
        )


        response = requests.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0"
            },
            timeout=10
        )


        data = response.json()


        price = (
            data["chart"]
            ["result"][0]
            ["meta"]
            ["regularMarketPrice"]
        )


        return float(price)


    except Exception:

        return None
