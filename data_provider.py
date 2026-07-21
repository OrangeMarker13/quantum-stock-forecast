import os
import time
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


REQUEST_TIMEOUT = 10



# ============================================================
# HTTP REQUEST HELPER
# ============================================================


def yahoo_request(
    url,
    retries=3
):

    for attempt in range(retries):

        try:

            response = requests.get(
                url,
                headers=YAHOO_HEADERS,
                timeout=REQUEST_TIMEOUT
            )


            if response.status_code == 200:

                return response.json()



        except Exception as error:

            print(
                f"Yahoo request attempt {attempt + 1} failed:",
                error
            )


        time.sleep(1)



    return None




# ============================================================
# DATA STORAGE
# ============================================================


def get_file_path(
    ticker
):

    return os.path.join(
        DATA_FOLDER,
        f"{ticker.upper()}.csv"
    )





def save_stock_data(
    ticker,
    dataframe
):

    try:

        if dataframe is None:

            return


        if dataframe.empty:

            return



        dataframe.to_csv(

            get_file_path(
                ticker
            ),

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

        filepath = get_file_path(
            ticker
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
            "Load saved data error:",
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

            return (
                f"{value / 1_000_000_000:.2f}B"
            )



        if value >= 1_000_000:

            return (
                f"{value / 1_000_000:.2f}M"
            )



        if value >= 1_000:

            return (
                f"{value / 1_000:.2f}K"
            )



        return str(int(value))



    except Exception:

        return "N/A"
    # ============================================================
# DATA CLEANING
# ============================================================


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



    if "Volume" in data.columns:


        data["Volume"] = pd.to_numeric(

            data["Volume"],

            errors="coerce"

        )



    data = data.ffill()

    data = data.bfill()



    return data





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



    # Moving averages

    data["SMA20"] = (

        data["Close"]

        .rolling(

            20,

            min_periods=1

        )

        .mean()

    )



    data["SMA50"] = (

        data["Close"]

        .rolling(

            50,

            min_periods=1

        )

        .mean()

    )





    # ========================================================
    # RSI
    # ========================================================


    delta = data["Close"].diff()



    gain = delta.clip(

        lower=0

    )


    loss = -delta.clip(

        upper=0

    )



    avg_gain = (

        gain

        .rolling(

            14,

            min_periods=1

        )

        .mean()

    )



    avg_loss = (

        loss

        .rolling(

            14,

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



    data["RSI"] = (

        data["RSI"]

        .fillna(

            50

        )

    )





    # ========================================================
    # Volatility
    # ========================================================


    data["Volatility"] = (

        data["Return"]

        .rolling(

            20,

            min_periods=5

        )

        .std()

    )



    data["Volatility"] = (

        data["Volatility"]

        .fillna(

            data["Return"].std()

        )

        .fillna(

            0.01

        )

    )





    # ========================================================
    # Momentum
    # ========================================================


    data["Momentum"] = (

        data["Close"]

        /

        data["Close"].shift(

            20

        )

        -

        1

    )



    data["Momentum"] = (

        data["Momentum"]

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





    # ========================================================
    # Volume Change
    # ========================================================


    if "Volume" in data.columns:


        data["Volume_Change"] = (

            data["Volume"]

            .pct_change()

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

    ttl=900,

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



    # Yahoo chart API

    url = (

        "https://query1.finance.yahoo.com/v8/finance/chart/"

        f"{ticker}"

        "?range=2y&interval=1d"

    )



    data = yahoo_request(

        url

    )



    try:


        if data:


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



            if result:


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



                if not dataframe.empty:


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

            "Yahoo parsing error:",

            error

        )





    # ========================================================
    # FALLBACK TO SAVED DATA
    # ========================================================


    saved = load_saved_data(

        ticker

    )



    saved = clean_market_data(

        saved

    )



    if not saved.empty:


        if "RSI" not in saved.columns:


            saved = add_indicators(

                saved

            )



        return saved



    return pd.DataFrame()





# ============================================================
# LIVE PRICE DATA
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

        "https://query1.finance.yahoo.com/v8/finance/chart/"

        f"{ticker}"

    )



    data = yahoo_request(

        url

    )



    try:


        if not data:

            return None



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



        price = meta.get(

            "regularMarketPrice"

        )



        if price is None:


            price = meta.get(

                "chartPreviousClose"

            )



        previous_close = meta.get(

            "previousClose"

        )



        if price is None:

            return None



        price = float(

            price

        )



        if previous_close:


            previous_close = float(

                previous_close

            )



            change_percent = (

                (

                    price -

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

            price,



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

        "https://query1.finance.yahoo.com/v7/finance/quote?"

        f"symbols={ticker}"

    )



    data = yahoo_request(

        url

    )



    try:


        if not data:

            return default



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



    if live_data.get(

        "price"

    ) is None:

        return "Unavailable"



    return "Market Data Active"





# ============================================================
# VALIDATION
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
# CACHE CONTROL
# ============================================================


def clear_data_cache():

    try:


        st.cache_data.clear()



    except Exception as error:


        print(

            "Cache clearing error:",

            error

        )





# ============================================================
# SAFE NUMBER CONVERSION
# ============================================================


def safe_float(
    value,
    default=0.0
):


    try:


        if value is None:

            return default



        value = float(

            value

        )



        if np.isnan(value):

            return default



        return value



    except Exception:


        return default





# ============================================================
# MARKET SUMMARY
# ============================================================


def get_market_summary(
    ticker
):


    live = get_live_price(

        ticker

    )



    company = get_company_info(

        ticker

    )



    historical = get_stock_data(

        ticker

    )



    return {


        "ticker":

        ticker.upper(),



        "company":

        company.get(

            "name",

            ticker

        ),



        "price":

        live.get(

            "price"

        )

        if live

        else None,



        "daily_change":

        live.get(

            "change_percent"

        )

        if live

        else None,



        "historical_points":

        len(

            historical

        )

        if historical is not None

        else 0

    }





# ============================================================
# LOCAL TEST
# ============================================================


if __name__ == "__main__":


    test = get_stock_data(

        "AAPL"

    )


    print(

        test.head()

    )


    print(

        test.shape

    )


    live = get_live_price(

        "AAPL"

    )


    print(

        live

    )
