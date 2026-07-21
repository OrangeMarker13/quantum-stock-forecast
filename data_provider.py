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
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"

}



# ============================================================
# REQUEST HELPER
# ============================================================


def yahoo_request(url):

    try:

        response = requests.get(

            url,

            headers=YAHOO_HEADERS,

            timeout=15

        )


        response.raise_for_status()


        return response.json()



    except Exception as error:

        print(

            "Yahoo request error:",

            error

        )


        return None





# ============================================================
# DATA STORAGE
# ============================================================


def save_stock_data(ticker, dataframe):

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





def load_saved_data(ticker):

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


def format_price(value):

    if value is None:

        return "N/A"


    try:

        return f"${float(value):,.2f}"


    except Exception:

        return "N/A"





def format_percent(value):

    if value is None:

        return "N/A"


    try:

        return f"{float(value):+.2f}%"


    except Exception:

        return "N/A"





def format_volume(value):

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



    except Exception:

        return "N/A"
    # ============================================================
# TECHNICAL INDICATORS
# ============================================================


def add_indicators(dataframe):

    if dataframe is None:

        return pd.DataFrame()



    data = dataframe.copy()



    if data.empty:

        return data



    if "Close" not in data.columns:

        return data





    # ========================================================
    # RETURNS
    # ========================================================


    data["Return"] = (

        data["Close"]

        .pct_change()

    )



    data["Log_Return"] = np.log(

        data["Close"] /

        data["Close"].shift(1)

    )



    data["Log_Return"] = data["Log_Return"].replace(

        [

            np.inf,

            -np.inf

        ],

        np.nan

    ).fillna(0)





    # ========================================================
    # MOVING AVERAGES
    # ========================================================


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

            (1 + rs)

        )

    )



    data["RSI"] = data["RSI"].fillna(

        50

    )





    # ========================================================
    # VOLATILITY
    # ========================================================


    data["Volatility"] = (

        data["Log_Return"]

        .rolling(

            window=20,

            min_periods=5

        )

        .std()

    )



    data["Volatility"] = data["Volatility"].fillna(

        data["Log_Return"].std()

    )



    data["Volatility"] = data["Volatility"].fillna(

        0

    )





    # ========================================================
    # MOMENTUM
    # ========================================================


    data["Momentum"] = (

        data["Close"] /

        data["Close"].shift(20)

        -

        1

    )



    data["Momentum"] = data["Momentum"].replace(

        [

            np.inf,

            -np.inf

        ],

        np.nan

    ).fillna(0)





    # ========================================================
    # VOLUME ANALYSIS
    # ========================================================


    if "Volume" in data.columns:


        data["Volume_Change"] = (

            data["Volume"]

            .pct_change()

        )


        data["Volume_Change"] = data["Volume_Change"].replace(

            [

                np.inf,

                -np.inf

            ],

            np.nan

        ).fillna(0)



    else:


        data["Volume_Change"] = 0





    return data





# ============================================================
# ADVANCED MARKET FEATURES
# ============================================================


def add_advanced_features(dataframe):


    if dataframe is None:

        return pd.DataFrame()



    data = dataframe.copy()



    if data.empty:

        return data



    try:


        # ====================================================
        # TREND DISTANCE
        # ====================================================


        data["SMA20_Distance"] = (

            data["Close"] -

            data["SMA20"]

        ) / data["SMA20"]



        data["SMA50_Distance"] = (

            data["Close"] -

            data["SMA50"]

        ) / data["SMA50"]



        data["SMA20_Distance"] = data["SMA20_Distance"].replace(

            [

                np.inf,

                -np.inf

            ],

            np.nan

        ).fillna(0)



        data["SMA50_Distance"] = data["SMA50_Distance"].replace(

            [

                np.inf,

                -np.inf

            ],

            np.nan

        ).fillna(0)
                # ====================================================
        # VOLATILITY REGIME
        # ====================================================


        data["Volatility_Regime"] = (

            data["Volatility"]

            .rolling(

                window=60,

                min_periods=10

            )

            .mean()

        )



        data["Volatility_Regime"] = data["Volatility_Regime"].fillna(

            data["Volatility"].mean()

        )





        # ====================================================
        # PRICE TREND SCORE
        # ====================================================


        trend_score = np.zeros(

            len(data)

        )



        trend_score += np.where(

            data["Close"] > data["SMA20"],

            1,

            -1

        )



        trend_score += np.where(

            data["Close"] > data["SMA50"],

            1,

            -1

        )



        trend_score += np.where(

            data["Momentum"] > 0,

            1,

            -1

        )



        data["Trend_Score"] = trend_score / 3





        # ====================================================
        # MARKET REGIME CLASSIFICATION
        # ====================================================


        data["Market_Regime"] = "Neutral"



        data.loc[

            data["Trend_Score"] > 0.33,

            "Market_Regime"

        ] = "Bullish"



        data.loc[

            data["Trend_Score"] < -0.33,

            "Market_Regime"

        ] = "Bearish"





        return data



    except Exception as error:


        print(

            "Advanced feature error:",

            error

        )


        return data





# ============================================================
# CLEAN DATA
# ============================================================


def clean_market_data(dataframe):


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

def get_stock_data(ticker):


    ticker = (

        ticker

        .upper()

        .strip()

    )



    url = (

        "https://query1.finance.yahoo.com/"

        f"v8/finance/chart/{ticker}"

        "?range=2y&interval=1d"

    )



    try:


        json_data = yahoo_request(

            url

        )



        if json_data is None:


            return load_saved_data(

                ticker

            )



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


            return load_saved_data(

                ticker

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



        dataframe = add_advanced_features(

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


        saved_data = load_saved_data(

            ticker

        )



        if saved_data.empty:


            return pd.DataFrame()



        saved_data = clean_market_data(

            saved_data

        )



        saved_data = add_indicators(

            saved_data

        )



        saved_data = add_advanced_features(

            saved_data

        )



        return saved_data





# ============================================================
# LIVE MARKET DATA
# ============================================================


@st.cache_data(

    ttl=15,

    max_entries=200

)

def get_live_price(ticker):


    ticker = (

        ticker

        .upper()

        .strip()

    )



    url = (

        "https://query1.finance.yahoo.com/"

        f"v8/finance/chart/{ticker}"

    )



    try:


        json_data = yahoo_request(

            url

        )



        if json_data is None:


            return None



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



        if current_price is None:


            current_price = meta.get(

                "chartPreviousClose"

            )



        if current_price is None:


            return None



        current_price = float(

            current_price

        )



        if previous_close:


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

def get_company_info(ticker):


    ticker = ticker.upper().strip()



    return {


        "name":

        ticker,


        "exchange":

        "Unknown",


        "currency":

        "USD"

    }





# ============================================================
# MARKET STATUS
# ============================================================


def get_market_status(live_data):


    if live_data is None:


        return "Unavailable"



    if live_data.get(

        "price"

    ) is None:


        return "Unavailable"



    return "Live Data Connected"





# ============================================================
# VALIDATION
# ============================================================


def validate_market_data(dataframe):


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
# CACHE RESET
# ============================================================


def clear_data_cache():


    try:


        st.cache_data.clear()



    except Exception as error:


        print(

            "Cache clear error:",

            error

        )





# ============================================================
# SAFE FLOAT
# ============================================================


def safe_float(value, default=0.0):


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
# SUMMARY
# ============================================================


def get_market_summary(ticker):


    live = get_live_price(

        ticker

    )



    historical = get_stock_data(

        ticker

    )



    return {


        "ticker":

        ticker.upper(),



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

    }





# ============================================================
# TEST
# ============================================================


if __name__ == "__main__":


    data = get_stock_data(

        "AAPL"

    )


    print(

        data.tail()

    )


    live = get_live_price(

        "AAPL"

    )


    print(

        live

    )
