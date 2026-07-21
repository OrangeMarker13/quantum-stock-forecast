import os
import time
import requests
import pandas as pd
import numpy as np
import streamlit as st


# ============================================================
# SETTINGS
# ============================================================

DATA_FOLDER = "data"

CACHE_DAYS = 1

os.makedirs(
    DATA_FOLDER,
    exist_ok=True
)


# ============================================================
# LOCAL STORAGE
# ============================================================

def get_file_path(ticker):

    return os.path.join(
        DATA_FOLDER,
        f"{ticker}.csv"
    )



def save_data(
    ticker,
    data
):

    try:

        path = get_file_path(
            ticker
        )

        data.to_csv(
            path,
            index=False
        )

        return True


    except Exception:

        return False



def load_saved_data(
    ticker
):

    try:

        path = get_file_path(
            ticker
        )


        if not os.path.exists(path):

            return None



        data = pd.read_csv(
            path
        )


        if "Close" not in data.columns:

            return None



        data["Close"] = (
            pd.to_numeric(
                data["Close"],
                errors="coerce"
            )
        )


        data = (
            data
            .dropna()
            .reset_index(drop=True)
        )


        if len(data) < 20:

            return None



        return data


    except Exception:

        return None



# ============================================================
# PROVIDER 1
# STOOQ FREE MARKET DATA
# ============================================================

def stooq_provider(
    ticker
):

    try:

        symbol = ticker.lower()

        if "-" in symbol:

            symbol = symbol.replace(
                "-",
                "."
            )


        url = (
            "https://stooq.com/q/d/l/"
            f"?s={symbol}&d1=&d2="
        )


        response = requests.get(
            url,
            timeout=5
        )


        if response.status_code != 200:

            return None



        from io import StringIO


        data = pd.read_csv(
            StringIO(
                response.text
            )
        )


        if "Close" not in data.columns:

            return None



        data = data[
            ["Close"]
        ]


        data["Close"] = (
            pd.to_numeric(
                data["Close"],
                errors="coerce"
            )
        )


        data = (
            data
            .dropna()
            .tail(500)
        )


        if len(data) < 20:

            return None



        return data



    except Exception:

        return None



# ============================================================
# PROVIDER 2
# YAHOO BACKUP
# ============================================================

def yahoo_provider(
    ticker
):

    try:

        import yfinance as yf


        data = yf.download(
            ticker,
            period="2y",
            interval="1d",
            progress=False,
            auto_adjust=True
        )


        if data.empty:

            return None



        close = data["Close"]


        if isinstance(
            close,
            pd.DataFrame
        ):

            close = close.iloc[:,0]



        result = pd.DataFrame(
            {
                "Close": close
            }
        )


        result["Close"] = (
            pd.to_numeric(
                result["Close"],
                errors="coerce"
            )
        )


        result = (
            result
            .dropna()
            .reset_index(drop=True)
        )


        if len(result) < 20:

            return None



        return result



    except Exception:

        return None



# ============================================================
# MAIN DATA ENGINE
# ============================================================


@st.cache_data(
    ttl=3600,
    max_entries=200
)
def get_stock_data(
    ticker
):


    ticker = (
        ticker
        .upper()
        .strip()
    )



    # Check local storage first

    stored = load_saved_data(
        ticker
    )


    if stored is not None:

        return stored["Close"]



    # Provider order

    providers = [

        stooq_provider,

        yahoo_provider

    ]



    for provider in providers:


        data = provider(
            ticker
        )


        if data is not None:


            save_data(
                ticker,
                data
            )


            return data["Close"]



        time.sleep(
            0.5
        )



    return pd.Series(
        dtype=float
    )



# ============================================================
# LIVE PRICE
# ============================================================


@st.cache_data(
    ttl=60,
    max_entries=200
)
def get_live_price(
    ticker
):


    try:


        url = (
            "https://query1.finance.yahoo.com/"
            f"v8/finance/chart/{ticker}"
        )


        response = requests.get(
            url,
            timeout=5
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


    except Exception:

        return None
