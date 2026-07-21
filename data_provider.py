import os
import time
import requests
import pandas as pd
import streamlit as st


# ============================================================
# SETTINGS
# ============================================================

DATA_FOLDER = "data"

os.makedirs(
    DATA_FOLDER,
    exist_ok=True
)



# ============================================================
# LOCAL CACHE
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

        data.to_csv(
            get_file_path(ticker),
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



        data["Close"] = pd.to_numeric(
            data["Close"],
            errors="coerce"
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
# STOOQ
# ============================================================

def stooq_provider(
    ticker
):

    try:

        symbol = (
            ticker
            .lower()
            .replace(
                "-",
                "."
            )
        )


        url = (
            "https://stooq.com/q/d/l/"
            f"?s={symbol}&i=d"
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


        data["Close"] = pd.to_numeric(
            data["Close"],
            errors="coerce"
        )


        data = (
            data
            .dropna()
            .tail(500)
            .reset_index(drop=True)
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


        result["Close"] = pd.to_numeric(
            result["Close"],
            errors="coerce"
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
# MAIN MARKET DATA ENGINE
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


    # Check saved database first

    saved = load_saved_data(
        ticker
    )


    if saved is not None:

        return (
            saved["Close"]
            .astype(float)
        )



    providers = [

        stooq_provider,

        yahoo_provider

    ]



    for provider in providers:


        try:

            data = provider(
                ticker
            )


        except Exception:

            data = None



        if data is not None:


            save_data(
                ticker,
                data
            )


            return (
                data["Close"]
                .dropna()
                .astype(float)
            )



        time.sleep(
            0.5
        )



    # Final failure protection

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


        result = response.json()


        price = (
            result
            ["chart"]
            ["result"][0]
            ["meta"]
            ["regularMarketPrice"]
        )


        return float(
            price
        )



    except Exception:


        # fallback to stored data

        try:

            history = get_stock_data(
                ticker
            )


            if not history.empty:

                return float(
                    history.iloc[-1]
                )


        except Exception:

            pass



        return None
