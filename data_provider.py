import os
import requests
import pandas as pd
import numpy as np
import streamlit as st


# ============================================================
# CONFIGURATION
# ============================================================


DATA_FOLDER = "data"



if not os.path.exists(DATA_FOLDER):

    os.makedirs(DATA_FOLDER)



YAHOO_HEADERS = {

    "User-Agent":

    "Mozilla/5.0"

}



# ============================================================
# LOCAL STORAGE
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
# TECHNICAL INDICATORS
# ============================================================


def add_indicators(

    data

):


    data = data.copy()



    if "Close" not in data.columns:


        return pd.DataFrame()



    # Daily return


    data["Return"] = (

        data["Close"]

        .pct_change()

    )



    # Moving averages


    data["SMA20"] = (

        data["Close"]

        .rolling(

            window=20

        )

        .mean()

    )



    data["SMA50"] = (

        data["Close"]

        .rolling(

            window=50

        )

        .mean()

    )



    # RSI


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

        .rolling(

            window=14

        )

        .mean()

    )



    avg_loss = (

        loss

        .rolling(

            window=14

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



    # Volatility


    data["Volatility"] = (

        data["Return"]

        .rolling(

            window=20

        )

        .std()

    )



    # Momentum


    data["Momentum"] = (

        data["Close"]

        /

        data["Close"]

        .shift(20)

        -

        1

    )



    # Volume movement


    if "Volume" in data.columns:


        data["Volume_Change"] = (

            data["Volume"]

            .pct_change()

        )


    else:


        data["Volume_Change"] = 0
# ============================================================
# HISTORICAL MARKET DATA
# ============================================================


@st.cache_data(

    ttl=3600,

    max_entries=100

)

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

            headers=YAHOO_HEADERS,

            timeout=15

        )



        if response.status_code != 200:


            saved = load_saved_data(

                ticker

            )


            return saved



        json_data = response.json()



        chart = (

            json_data

            .get(

                "chart",

                {}

            )

        )



        result = chart.get(

            "result"

        )



        if not result:


            saved = load_saved_data(

                ticker

            )


            return saved



        result = result[0]



        timestamps = result.get(

            "timestamp"

        )



        indicators = (

            result

            .get(

                "indicators",

                {}

            )

        )



        quote = (

            indicators

            .get(

                "quote",

                [{}]

            )[0]

        )



        closes = quote.get(

            "close"

        )



        volumes = quote.get(

            "volume"

        )



        if (

            timestamps is None

            or

            closes is None

        ):


            saved = load_saved_data(

                ticker

            )


            return saved



        dataframe = pd.DataFrame(

            {

                "Date":

                pd.to_datetime(

                    timestamps,

                    unit="s"

                ),



                "Close":

                closes,



                "Volume":

                volumes

            }

        )



        dataframe = (

            dataframe

            .dropna(

                subset=[

                    "Close"

                ]

            )

        )



        if dataframe.empty:


            saved = load_saved_data(

                ticker

            )


            return saved



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



        saved = load_saved_data(

            ticker

        )



        return saved
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


    try:


        url = (

            f"https://query1.finance.yahoo.com/"

            f"v8/finance/chart/{ticker}"

        )



        response = requests.get(

            url,

            headers=YAHOO_HEADERS,

            timeout=10

        )



        if response.status_code != 200:


            return None



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



        current_price = meta.get(

            "regularMarketPrice"

        )



        previous_close = meta.get(

            "previousClose"

        )



        day_high = meta.get(

            "regularMarketDayHigh"

        )



        day_low = meta.get(

            "regularMarketDayLow"

        )



        volume = meta.get(

            "regularMarketVolume"

        )



        market_state = meta.get(

            "marketState",

            "UNKNOWN"

        )



        if current_price is None:


            return None



        if previous_close is not None:


            change = (

                current_price -

                previous_close

            )



            change_percent = (

                change /

                previous_close

            ) * 100



        else:


            change = 0


            change_percent = 0



        return {


            "ticker":

            ticker,



            "price":

            float(current_price),



            "change":

            float(change),



            "change_percent":

            float(change_percent),



            "previous_close":

            float(previous_close)

            if previous_close

            else None,



            "day_high":

            float(day_high)

            if day_high

            else None,



            "day_low":

            float(day_low)

            if day_low

            else None,



            "volume":

            int(volume)

            if volume

            else None,



            "market_state":

            market_state

        }



    except Exception as error:


        print(

            "Live market data error:",

            error

        )


        return None
# ============================================================
# COMPANY INFORMATION
# ============================================================


@st.cache_data(

    ttl=86400,

    max_entries=100

)

def get_company_info(

    ticker

):


    try:


        url = (

            f"https://query1.finance.yahoo.com/"

            f"v10/finance/quoteSummary/"

            f"{ticker}"

            f"?modules=assetProfile"

        )



        response = requests.get(

            url,

            headers=YAHOO_HEADERS,

            timeout=10

        )



        if response.status_code != 200:


            return {


                "name":

                ticker,



                "sector":

                "Unknown",



                "industry":

                "Unknown"

            }



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



        return {


            "name":

            profile.get(

                "longName",

                ticker

            ),



            "sector":

            profile.get(

                "sector",

                "Unknown"

            ),



            "industry":

            profile.get(

                "industry",

                "Unknown"

            )

        }



    except Exception as error:


        print(

            "Company info error:",

            error

        )


        return {


            "name":

            ticker,



            "sector":

            "Unknown",



            "industry":

            "Unknown"

        }





# ============================================================
# MARKET STATUS
# ============================================================


def get_market_status(

    live_data

):


    if live_data is None:


        return "DATA UNAVAILABLE"



    state = live_data.get(

        "market_state",

        "UNKNOWN"

    )



    states = {


        "REGULAR":

        "MARKET OPEN",



        "PRE":

        "PRE-MARKET",



        "POST":

        "AFTER HOURS",



        "CLOSED":

        "MARKET CLOSED"

    }



    return states.get(

        state,

        state

    )





# ============================================================
# SAFE NUMBER FORMATTERS
# ============================================================


def format_price(

    value

):


    if value is None:


        return "N/A"



    return f"${value:,.2f}"





def format_percent(

    value

):


    if value is None:


        return "N/A"



    return f"{value:+.2f}%"





def format_volume(

    value

):


    if value is None:


        return "N/A"



    if value >= 1_000_000_000:


        return f"{value / 1_000_000_000:.2f}B"



    if value >= 1_000_000:


        return f"{value / 1_000_000:.2f}M"



    if value >= 1_000:


        return f"{value / 1_000:.2f}K"



    return str(value)


    return data
