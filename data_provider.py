import os
import requests
import pandas as pd
import numpy as np
import streamlit as st


# ============================================================
# CONFIGURATION
# ============================================================

DATA_FOLDER = "data"

os.makedirs(
    DATA_FOLDER,
    exist_ok=True
)


YAHOO_HEADERS = {
    "User-Agent": "Mozilla/5.0"
}



# ============================================================
# DATA STORAGE
# ============================================================


def save_stock_data(
    ticker,
    dataframe
):

    try:

        if dataframe is None or dataframe.empty:
            return


        filepath = os.path.join(
            DATA_FOLDER,
            f"{ticker}.csv"
        )


        dataframe.to_csv(
            filepath,
            index=False
        )


    except Exception as error:

        print(
            "Save data error:",
            error
        )




def load_saved_data(
    ticker
):

    try:

        filepath = os.path.join(
            DATA_FOLDER,
            f"{ticker}.csv"
        )


        if not os.path.exists(filepath):

            return pd.DataFrame()



        dataframe = pd.read_csv(
            filepath
        )


        if "Date" in dataframe.columns:

            dataframe["Date"] = pd.to_datetime(
                dataframe["Date"],
                errors="coerce"
            )


        return dataframe



    except Exception as error:

        print(
            "Load data error:",
            error
        )

        return pd.DataFrame()




# ============================================================
# FORMATTING FUNCTIONS
# ============================================================


def format_price(
    value
):

    try:

        if value is None:
            return "N/A"


        return f"${float(value):,.2f}"


    except Exception:

        return "N/A"




def format_percent(
    value
):

    try:

        if value is None:
            return "N/A"


        return f"{float(value):+.2f}%"


    except Exception:

        return "N/A"




def format_volume(
    value
):

    try:

        if value is None:
            return "N/A"


        value = float(value)


        if value >= 1_000_000_000:

            return f"{value / 1_000_000_000:.2f}B"



        if value >= 1_000_000:

            return f"{value / 1_000_000:.2f}M"



        if value >= 1_000:

            return f"{value / 1_000:.2f}K"



        return str(int(value))



    except Exception:

        return "N/A"




# ============================================================
# SAFE NUMERIC HELPERS
# ============================================================


def safe_float(
    value,
    default=0.0
):

    try:

        if value is None:
            return default


        value = float(value)


        if np.isnan(value):

            return default


        return value



    except Exception:

        return default




def clean_market_data(
    dataframe
):

    if dataframe is None:

        return pd.DataFrame()



    if dataframe.empty:

        return pd.DataFrame()



    data = dataframe.copy()



    data = data.replace(
        [
            np.inf,
            -np.inf
        ],
        np.nan
    )



    if "Close" in data.columns:

        data["Close"] = pd.to_numeric(
            data["Close"],
            errors="coerce"
        )


        data = data.dropna(
            subset=[
                "Close"
            ]
        )



    data = data.ffill()

    data = data.bfill()

# ============================================================
# TECHNICAL INDICATORS
# ============================================================


def add_indicators(
    dataframe
):

    data = dataframe.copy()



    if data.empty:

        return data



    if "Close" not in data.columns:

        return data



    # Daily returns

    data["Return"] = (

        data["Close"]

        .pct_change()

    )



    # Moving averages

    data["SMA20"] = (

        data["Close"]

        .rolling(

            window=20,

            min_periods=1

        )

        .mean()

    )



    data["SMA50"] = (

        data["Close"]

        .rolling(

            window=50,

            min_periods=1

        )

        .mean()

    )



    # ========================================================
    # RSI
    # ========================================================


    delta = data["Close"].diff()



    gains = delta.clip(

        lower=0

    )


    losses = -delta.clip(

        upper=0

    )



    avg_gain = (

        gains

        .rolling(

            window=14,

            min_periods=1

        )

        .mean()

    )



    avg_loss = (

        losses

        .rolling(

            window=14,

            min_periods=1

        )

        .mean()

    )



    rs = (

        avg_gain /

        avg_loss.replace(

            0,

            np.nan

        )

    )



    data["RSI"] = (

        100 -

        (

            100 /

            (

                1 +

                rs

            )

        )

    )



    data["RSI"] = data["RSI"].fillna(

        50

    )



    # ========================================================
    # Volatility
    # ========================================================


    data["Volatility"] = (

        data["Return"]

        .rolling(

            window=20,

            min_periods=5

        )

        .std()

    )



    data["Volatility"] = data["Volatility"].fillna(

        data["Return"].std()

    )



    data["Volatility"] = data["Volatility"].fillna(

        0.01

    )



    # ========================================================
    # Momentum
    # ========================================================


    data["Momentum"] = (

        data["Close"]

        /

        data["Close"]

        .shift(20)

        -

        1

    )



    data["Momentum"] = data["Momentum"].fillna(

        0

    )



    # ========================================================
    # Volume Change
    # ========================================================


    if "Volume" in data.columns:


        data["Volume_Change"] = (

            data["Volume"]

            .pct_change()

        )


        data["Volume_Change"] = (

            data["Volume_Change"]

            .replace(

                [

                    np.inf,

                    -np.inf

                ],

                np.nan

            )

            .fillna(

                0

            )

        )


    else:


        data["Volume_Change"] = 0



    return data





# ============================================================
# HISTORICAL MARKET DATA
# ============================================================


@st.cache_data(

    ttl=300,

    max_entries=100

)

def get_stock_data(
    ticker
):

    ticker = (

        ticker

        .upper()

        .strip()

    )



    if not ticker:

        return pd.DataFrame()



    url = (

        "https://query1.finance.yahoo.com/"

        f"v8/finance/chart/{ticker}"

        "?range=2y&interval=1d"

    )



    try:


        response = requests.get(

            url,

            headers=YAHOO_HEADERS,

            timeout=15

        )



        response.raise_for_status()



        json_data = response.json()



        result = (

            json_data

            .get(

                "chart",

                {}

            )

            .get(

                "result"

            )

        )



        if not result:


            return add_indicators(

                clean_market_data(

                    load_saved_data(

                        ticker

                    )

                )

            )



        result = result[0]



        timestamps = result.get(

            "timestamp",

            []

        )



        quote = (

            result

            .get(

                "indicators",

                {}

            )

            .get(

                "quote",

                [{}]

            )[0]

        )



        dataframe = pd.DataFrame(

            {

                "Date":

                pd.to_datetime(

                    timestamps,

                    unit="s",

                    errors="coerce"

                ),


                "Close":

                quote.get(

                    "close",

                    []

                ),


                "Volume":

                quote.get(

                    "volume",

                    []

                )

            }

        )



        dataframe = clean_market_data(

            dataframe

        )



        dataframe = add_indicators(

            dataframe

        )



        if not dataframe.empty:


            save_stock_data(

                ticker,

                dataframe

            )



        return dataframe



    except Exception as error:


        print(

            "Historical data error:",

            error

        )


        saved = load_saved_data(

            ticker

        )


        saved = clean_market_data(

            saved

        )


        return add_indicators(

            saved

        )
    # ============================================================
# LIVE MARKET DATA
# ============================================================


@st.cache_data(

    ttl=15,

    max_entries=200

)

def get_live_price(
    ticker
):

    ticker = (

        ticker

        .upper()

        .strip()

    )


    if not ticker:

        return None



    url = (

        "https://query1.finance.yahoo.com/"

        f"v8/finance/chart/{ticker}"

    )



    try:


        response = requests.get(

            url,

            headers=YAHOO_HEADERS,

            timeout=10

        )


        response.raise_for_status()



        data = response.json()



        result = (

            data

            .get(

                "chart",

                {}

            )

            .get(

                "result"

            )

        )



        if not result:


            return None



        meta = result[0].get(

            "meta",

            {}

        )



        current_price = meta.get(

            "regularMarketPrice"

        )



        previous_close = meta.get(

            "previousClose"

        )



        # Fallback if regular market price is missing

        if current_price is None:


            current_price = meta.get(

                "chartPreviousClose"

            )



        if current_price is None:


            return None



        current_price = float(

            current_price

        )



        if previous_close is not None:


            previous_close = float(

                previous_close

            )


            change_percent = (

                (

                    current_price -

                    previous_close

                )

                /

                previous_close

            ) * 100



        else:


            previous_close = None

            change_percent = 0



        return {


            "price":

            current_price,



            "previous_close":

            previous_close,



            "change_percent":

            change_percent

        }



    except Exception as error:


        print(

            "Live price error:",

            error

        )


        return None





# ============================================================
# COMPANY INFORMATION
# ============================================================


@st.cache_data(

    ttl=3600,

    max_entries=100

)

def get_company_info(
    ticker
):


    ticker = (

        ticker

        .upper()

        .strip()

    )



    default = {


        "name":

        ticker,



        "exchange":

        "Unknown",



        "currency":

        "USD"

    }



    url = (

        "https://query1.finance.yahoo.com/"

        f"v7/finance/quote?symbols={ticker}"

    )



    try:


        response = requests.get(

            url,

            headers=YAHOO_HEADERS,

            timeout=10

        )


        response.raise_for_status()



        data = response.json()



        results = (

            data

            .get(

                "quoteResponse",

                {}

            )

            .get(

                "result",

                []

            )

        )



        if not results:


            return default



        quote = results[0]



        return {


            "name":

            quote.get(

                "longName",

                quote.get(

                    "shortName",

                    ticker

                )

            ),



            "exchange":

            quote.get(

                "exchange",

                "Unknown"

            ),



            "currency":

            quote.get(

                "currency",

                "USD"

            )

        }



    except Exception as error:


        print(

            "Company info error:",

            error

        )


        return default





# ============================================================
# MARKET STATUS
# ============================================================


def get_market_status(
    live_data
):


    if live_data is None:


        return "Unavailable"



    price = live_data.get(

        "price"

    )



    if price is None:


        return "Unavailable"



    return "Data Available"
# ============================================================
# DATA VALIDATION
# ============================================================


def validate_market_data(
    dataframe
):


    if dataframe is None:

        return False



    if dataframe.empty:

        return False



    if "Close" not in dataframe.columns:

        return False



    if len(dataframe) < 20:

        return False



    return True





# ============================================================
# CACHE MANAGEMENT
# ============================================================


def clear_data_cache():

    """
    Clears Streamlit cached data.

    Use when:
    - Yahoo Finance data is stale
    - Switching many tickers
    - Testing changes
    """


    try:


        st.cache_data.clear()



    except Exception as error:


        print(

            "Cache clear error:",

            error

        )





# ============================================================
# MARKET SUMMARY
# ============================================================


def get_market_summary(
    ticker
):


    ticker = (

        ticker

        .upper()

        .strip()

    )



    live = get_live_price(

        ticker

    )


    company = get_company_info(

        ticker

    )


    historical = get_stock_data(

        ticker

    )



    summary = {


        "ticker":

        ticker,



        "company":

        company.get(

            "name",

            ticker

        ),



        "price":

        None,



        "daily_change":

        None,



        "historical_points":

        0

    }



    if historical is not None:


        summary["historical_points"] = len(

            historical

        )



    if live:


        summary["price"] = live.get(

            "price"

        )


        summary["daily_change"] = live.get(

            "change_percent"

        )



    return summary





# ============================================================
# MODULE TEST
# ============================================================


if __name__ == "__main__":


    test_data = get_stock_data(

        "AAPL"

    )


    print(

        test_data.tail()

    )


    live = get_live_price(

        "AAPL"

    )


    print(

        live

    )
if __name__ == "__main__":

    test = get_stock_data("AAPL")

    print(test.head())

    print(test.shape)

    print(test.columns)
