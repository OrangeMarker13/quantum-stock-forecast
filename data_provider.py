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
# DATA STORAGE
# ============================================================


def save_stock_data(

    ticker,

    dataframe

):


    try:


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

                dataframe["Date"]

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


        return f"{float(value):+.2f}%"



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



    data["Return"] = (

        data["Close"]

        .pct_change()

    )



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



    # --------------------------------------------------------
    # RSI
    # --------------------------------------------------------


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

            (1 + rs)

        )

    )



    data["RSI"] = data["RSI"].fillna(

        50

    )



    # --------------------------------------------------------
    # VOLATILITY
    # --------------------------------------------------------


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



    # --------------------------------------------------------
    # MOMENTUM
    # --------------------------------------------------------


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



    # --------------------------------------------------------
    # VOLUME CHANGE
    # --------------------------------------------------------


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
# CLEAN DATA
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


        data = data.dropna(

            subset=[

                "Close"

            ]

        )



    data = data.ffill()



    data = data.bfill()



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


    ticker = ticker.upper().strip()



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


            return clean_market_data(

                load_saved_data(

                    ticker

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

                    unit="s"

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



        return clean_market_data(

            load_saved_data(

                ticker

            )

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


    ticker = ticker.upper().strip()



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



        if current_price is None:


            current_price = meta.get(

                "chartPreviousClose"

            )



        if current_price is None:


            return None



        if previous_close:


            change_percent = (

                (

                    float(current_price)

                    -

                    float(previous_close)

                )

                /

                float(previous_close)

            ) * 100



        else:


            change_percent = 0



        return {


            "price":

            float(current_price),



            "previous_close":

            (

                float(previous_close)

                if previous_close

                else None

            ),



            "change_percent":

            float(change_percent)

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


    ticker = ticker.upper().strip()



    url = (

        "https://query1.finance.yahoo.com/"

        f"v7/finance/quote?symbols={ticker}"

    )



    default = {


        "name":

        ticker,



        "exchange":

        "Unknown",



        "currency":

        "USD"

    }



    try:


        response = requests.get(

            url,

            headers=YAHOO_HEADERS,

            timeout=10

        )



        data = response.json()



        result = (

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



        if not result:


            return default



        quote = result[0]



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



    return "Data Available"
    # ============================================================
# DATA VALIDATION HELPERS
# ============================================================


def validate_market_data(

    dataframe

):


    if dataframe is None:


        return False



    if dataframe.empty:


        return False



    required_columns = [


        "Close"


    ]



    for column in required_columns:


        if column not in dataframe.columns:


            return False



    if len(dataframe) < 20:


        return False



    return True





# ============================================================
# FORCE FRESH DATA FUNCTIONS
# ============================================================


def clear_data_cache():

    """
    Clears Streamlit cached market data.

    Use this when:
    - Yahoo Finance data appears stale
    - A stock price is not updating
    - Testing a new ticker
    """


    try:


        st.cache_data.clear()



    except Exception as error:


        print(

            "Cache clear error:",

            error

        )





# ============================================================
# SAFE NUMERIC CONVERSION
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



    except:


        return default





# ============================================================
# EXPORT SUMMARY DATA
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



    summary = {


        "ticker":

        ticker.upper(),



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

        len(historical)

        if historical is not None

        else 0

    }



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


    test = get_stock_data(

        "AAPL"

    )


    print(

        test.tail()

    )

        return "N/A"
