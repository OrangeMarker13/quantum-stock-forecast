import requests
import pandas as pd
import streamlit as st
import time

from cache import save_cache, load_cache


# ============================================================
# API KEYS
# ============================================================

ALPHA_VANTAGE_KEY = st.secrets.get(
    "ALPHA_VANTAGE_KEY",
    ""
)

TWELVE_DATA_KEY = st.secrets.get(
    "TWELVE_DATA_KEY",
    ""
)

FMP_KEY = st.secrets.get(
    "FMP_KEY",
    ""
)



# ============================================================
# ALPHA VANTAGE
# ============================================================

def get_alpha_vantage(ticker):

    if not ALPHA_VANTAGE_KEY:
        return None


    try:

        url = (
            "https://www.alphavantage.co/query"
            "?function=TIME_SERIES_DAILY"
            f"&symbol={ticker}"
            "&outputsize=full"
            f"&apikey={ALPHA_VANTAGE_KEY}"
        )


        response = requests.get(
            url,
            timeout=10
        )


        data = response.json()


        if "Time Series (Daily)" not in data:

            return None



        prices = pd.DataFrame(
            data["Time Series (Daily)"]
        ).T



        prices.index = pd.to_datetime(
            prices.index
        )


        prices = prices.sort_index()



        close = (
            prices["4. close"]
            .astype(float)
        )


        return close



    except Exception:

        return None




# ============================================================
# TWELVE DATA
# ============================================================

def get_twelve_data(ticker):

    if not TWELVE_DATA_KEY:

        return None



    try:

        url = (
            "https://api.twelvedata.com/time_series"
            f"?symbol={ticker}"
            "&interval=1day"
            "&outputsize=500"
            f"&apikey={TWELVE_DATA_KEY}"
        )



        response = requests.get(
            url,
            timeout=10
        )



        data = response.json()



        if "values" not in data:

            return None



        df = pd.DataFrame(
            data["values"]
        )



        df["datetime"] = pd.to_datetime(
            df["datetime"]
        )



        df = df.sort_values(
            "datetime"
        )



        close = (
            df.set_index("datetime")["close"]
            .astype(float)
        )



        return close



    except Exception:

        return None




# ============================================================
# FINANCIAL MODELING PREP
# ============================================================

def get_fmp(ticker):

    if not FMP_KEY:

        return None



    try:

        url = (
            "https://financialmodelingprep.com/api/v3/"
            f"historical-price-full/{ticker}"
            f"?apikey={FMP_KEY}"
        )



        response = requests.get(
            url,
            timeout=10
        )



        data = response.json()



        if "historical" not in data:

            return None



        df = pd.DataFrame(
            data["historical"]
        )



        df["date"] = pd.to_datetime(
            df["date"]
        )



        df = df.sort_values(
            "date"
        )



        close = (
            df.set_index("date")["close"]
            .astype(float)
        )



        return close



    except Exception:

        return None




# ============================================================
# STOOQ BACKUP
# ============================================================

def get_stooq(ticker):

    try:

        url = (
            "https://stooq.com/q/d/l/"
            f"?s={ticker.lower()}&i=d"
        )



        df = pd.read_csv(
            url
        )



        if "Close" not in df.columns:

            return None



        df["Date"] = pd.to_datetime(
            df["Date"]
        )



        close = (
            df.set_index("Date")["Close"]
            .astype(float)
        )



        return close



    except Exception:

        return None




# ============================================================
# MAIN DATA ROUTER
# ============================================================

def get_stock_data(ticker):


    ticker = (
        ticker
        .upper()
        .strip()
    )



    # --------------------------------------------------------
    # CHECK CACHE FIRST
    # --------------------------------------------------------

    cached = load_cache(
        ticker
    )


    if cached is not None:


        st.info(
            f"Using cached data for {ticker}"
        )


        return cached




    # --------------------------------------------------------
    # PROVIDER FALLBACK ORDER
    # --------------------------------------------------------

    providers = [

        (
            "Alpha Vantage",
            get_alpha_vantage
        ),

        (
            "Twelve Data",
            get_twelve_data
        ),

        (
            "Financial Modeling Prep",
            get_fmp
        ),

        (
            "Stooq",
            get_stooq
        )

    ]




    for name, provider in providers:


        try:

            prices = provider(
                ticker
            )


        except Exception:

            prices = None




        if prices is not None:


            prices = (
                prices
                .dropna()
                .astype(float)
            )



            if len(prices) >= 20:


                save_cache(
                    ticker,
                    prices
                )



                st.success(
                    f"Data source: {name}"
                )



                return prices



        time.sleep(1)




    # --------------------------------------------------------
    # OLD CACHE FALLBACK
    # --------------------------------------------------------

    old_cache = load_cache(
        ticker,
        max_age_minutes=1440
    )



    if old_cache is not None:


        st.warning(
            "Using older cached market data."
        )


        return old_cache




    raise ValueError(
        f"No stock data found for {ticker}"
    )
