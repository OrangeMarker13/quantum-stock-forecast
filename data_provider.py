import os
import requests
import pandas as pd
import numpy as np
import streamlit as st
import datetime


# ============================================================
# CONFIGURATION
# ============================================================


DATA_FOLDER = "data"


if not os.path.exists(DATA_FOLDER):

    os.makedirs(
        DATA_FOLDER
    )



YAHOO_HEADERS = {

    "User-Agent":
    "Mozilla/5.0"

}





# ============================================================
# DATA STORAGE
# ============================================================


def save_stock_data(
    ticker,
    dataframe
):

    try:

        filepath = (
            f"{DATA_FOLDER}/{ticker}.csv"
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

        filepath = (
            f"{DATA_FOLDER}/{ticker}.csv"
        )


        if not os.path.exists(filepath):

            return pd.DataFrame()



        dataframe = pd.read_csv(

            filepath

        )


        return dataframe



    except Exception as error:


        print(

            "Load data error:",

            error

        )


        return pd.DataFrame()





# ============================================================
# FORMAT FUNCTIONS
# ============================================================


def format_price(
    value
):


    if value is None:

        return "N/A"



    try:

        return f"${float(value):,.2f}"


    except:


        return "N/A"





def format_percent(
    value
):


    if value is None:

        return "N/A"



    try:


        value = float(value)


        if value >= 0:

            return f"+{value:.2f}%"


        return f"{value:.2f}%"



    except:


        return "N/A"





def format_volume(
    value
):


    if value is None:

        return "N/A"



    try:

        value = float(value)



        if value >= 1_000_000_000:

            return f"{value / 1_000_000_000:.2f}B"



        if value >= 1_000_000:

            return f"{value / 1_000_000:.2f}M"



        if value >= 1_000:

            return f"{value / 1_000:.2f}K"



        return str(int(value))



    except:


        return "N/A"





# ============================================================
# TECHNICAL INDICATORS
# ============================================================


def add_indicators(
    data
):


    data = data.copy()



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



    delta = (

        data["Close"]

        .diff()

    )



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

            (1 + rs)

        )

    )
# ============================================================
# CONTINUED TECHNICAL INDICATORS
# ============================================================


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


    else:


        data["Volume_Change"] = 0



    # Prevent missing indicator crashes


    data = data.replace(

        [

            np.inf,

            -np.inf

        ],

        np.nan

    )



    data = data.ffill()



    data = data.bfill()



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



    try:


        url = (

            "https://query1.finance.yahoo.com/"

            "v8/finance/chart/"

            f"{ticker}"

            "?period1=1700000000"

            "&period2=9999999999"

            "&interval=1d"

        )



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


            raise Exception(

                "Yahoo returned no historical data"

            )



        result = result[0]



        timestamps = result.get(

            "timestamp"

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

                    unit="s"

                ),



                "Close":

                quote.get(

                    "close"

                ),



                "Volume":

                quote.get(

                    "volume"

                )

            }

        )



        dataframe = dataframe.dropna(

            subset=[

                "Close"

            ]

        )



        if len(dataframe) < 50:


            raise Exception(

                "Insufficient market history"

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

            "Historical data error:",

            error

        )



        saved_data = load_saved_data(

            ticker

        )



        if not saved_data.empty:


            return saved_data



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



    try:


        url = (

            "https://query1.finance.yahoo.com/"

            "v8/finance/chart/"

            f"{ticker}"

        )



        response = requests.get(

            url,

            headers=YAHOO_HEADERS,

            timeout=10

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


            return None



        meta = result[0].get(

            "meta",

            {}

        )



        price = meta.get(

            "regularMarketPrice"

        )



        previous_close = meta.get(

            "previousClose"

        )



        if price is None:


            return None



        change_percent = 0



        if previous_close:


            change_percent = (

                (

                    price -

                    previous_close

                )

                /

                previous_close

            ) * 100



        return {


            "price":

            float(price),



            "change_percent":

            float(change_percent),



            "previous_close":

            float(previous_close)

            if previous_close

            else None

        }

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


    try:


        url = (

            "https://query1.finance.yahoo.com/"

            "v10/finance/quoteSummary/"

            f"{ticker}"

            "?modules=assetProfile"

        )



        response = requests.get(

            url,

            headers=YAHOO_HEADERS,

            timeout=10

        )



        response.raise_for_status()



        data = response.json()



        profile = (

            data

            .get(

                "quoteSummary",

                {}

            )

            .get(

                "result",

                [{}]

            )[0]

            .get(

                "assetProfile",

                {}

            )

        )



        name = profile.get(

            "longName"

        )



        if name is None:


            name = ticker



        return {


            "ticker":

            ticker,



            "name":

            name,



            "sector":

            profile.get(

                "sector",

                "Unknown"

            ),



            "industry":

            profile.get(

                "industry",

                "Unknown"

            ),



            "description":

            profile.get(

                "longBusinessSummary",

                "No description available."

            )

        }



    except Exception as error:


        print(

            "Company info error:",

            error

        )



        return {


            "ticker":

            ticker,



            "name":

            ticker,



            "sector":

            "Unknown",



            "industry":

            "Unknown",



            "description":

            "No company information available."

        }





# ============================================================
# MARKET STATUS
# ============================================================


def get_market_status(

    live_data

):


    if live_data is None:


        return "Unknown"



    try:


        market_state = live_data.get(

            "marketState"

        )



        if market_state:


            return market_state



        return "Open / Data Available"



    except:


        return "Unknown"





# ============================================================
# IMPROVED LIVE MARKET DATA
# ============================================================


@st.cache_data(

    ttl=15,

    max_entries=200

)

def get_market_snapshot(

    ticker

):


    ticker = (

        ticker

        .upper()

        .strip()

    )


    try:


        url = (

            "https://query1.finance.yahoo.com/"

            "v7/finance/quote"

            f"?symbols={ticker}"

        )



        response = requests.get(

            url,

            headers=YAHOO_HEADERS,

            timeout=10

        )



        response.raise_for_status()



        data = response.json()



        quote = (

            data

            .get(

                "quoteResponse",

                {}

            )

            .get(

                "result",

                [{}]

            )[0]

        )



        price = quote.get(

            "regularMarketPrice"

        )



        previous = quote.get(

            "regularMarketPreviousClose"

        )



        change = quote.get(

            "regularMarketChangePercent"

        )



        if price is None:


            return None



        return {


            "ticker":

            ticker,



            "price":

            float(price),



            "previous_close":

            float(previous)

            if previous

            else None,



            "change_percent":

            float(change)

            if change

            else 0,



            "market_state":

            quote.get(

                "marketState",

                "Unknown"

            ),



            "volume":

            quote.get(

                "regularMarketVolume"

            )

        }



    except Exception as error:


        print(

            "Snapshot error:",

            error

        )


        return None
    # ============================================================
# FINAL FALLBACK UTILITIES
# ============================================================


def clean_market_dataframe(

    dataframe

):


    if dataframe is None:


        return pd.DataFrame()



    if dataframe.empty:


        return pd.DataFrame()



    dataframe = dataframe.copy()



    dataframe = dataframe.replace(

        [

            np.inf,

            -np.inf

        ],

        np.nan

    )



    dataframe = dataframe.dropna(

        subset=[

            "Close"

        ]

    )



    dataframe = dataframe.ffill()



    dataframe = dataframe.bfill()



    return dataframe





# ============================================================
# CACHE MANAGEMENT
# ============================================================


def clear_data_cache():


    try:


        st.cache_data.clear()



        return True



    except Exception as error:



        print(

            "Cache clear error:",

            error

        )



        return False





# ============================================================
# DATA VALIDATION
# ============================================================


def validate_stock_data(

    dataframe

):


    checks = {


        "exists":

        dataframe is not None,



        "not_empty":

        False

        if dataframe is None

        else not dataframe.empty,



        "has_close":

        False

        if dataframe is None

        else "Close" in dataframe.columns,



        "enough_history":

        False

        if dataframe is None

        else len(dataframe) >= 50

    }



    return checks





# ============================================================
# EXPORT AVAILABLE FUNCTIONS
# ============================================================


__all__ = [

    "get_stock_data",

    "get_live_price",

    "get_market_snapshot",

    "get_company_info",

    "get_market_status",

    "format_price",

    "format_percent",

    "format_volume",

    "clear_data_cache",

    "validate_stock_data"

]
