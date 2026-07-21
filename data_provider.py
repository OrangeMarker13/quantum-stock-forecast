# ============================================================
# DATA_PROVIDER.PY PART 1/6
# Quantum Equity Research Terminal
# Upgraded Data Infrastructure
# ============================================================


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


if not os.path.exists(DATA_FOLDER):

    os.makedirs(DATA_FOLDER)



YAHOO_HEADERS = {

    "User-Agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"

}



REQUEST_TIMEOUT = 15


MAX_RETRIES = 3





# ============================================================
# SAFE YAHOO REQUEST ENGINE
# ============================================================


def yahoo_request(url):


    for attempt in range(MAX_RETRIES):

        try:


            response = requests.get(

                url,

                headers=YAHOO_HEADERS,

                timeout=REQUEST_TIMEOUT

            )



            if response.status_code == 200:


                return response.json()



            else:


                print(

                    f"Yahoo request failed attempt {attempt+1}:",

                    response.status_code

                )



        except Exception as error:


            print(

                f"Yahoo request error attempt {attempt+1}:",

                error

            )



        time.sleep(1)



    return None





# ============================================================
# DATA STORAGE SYSTEM
# ============================================================


def save_stock_data(

    ticker,

    dataframe

):


    try:


        if dataframe is None:

            return



        if dataframe.empty:

            return



        filepath = os.path.join(

            DATA_FOLDER,

            f"{ticker.upper()}.csv"

        )



        dataframe.to_csv(

            filepath,

            index=False

        )



    except Exception as error:


        print(

            "Save stock data error:",

            error

        )







def load_saved_data(

    ticker

):


    try:


        filepath = os.path.join(

            DATA_FOLDER,

            f"{ticker.upper()}.csv"

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

            "Load stock data error:",

            error

        )


        return pd.DataFrame()





# ============================================================
# FORMATTING FUNCTIONS
# ============================================================


def format_price(value):


    try:


        if value is None:

            return "N/A"



        return f"${float(value):,.2f}"



    except Exception:


        return "N/A"







def format_percent(value):


    try:


        if value is None:

            return "N/A"



        return f"{float(value):+.2f}%"



    except Exception:


        return "N/A"







def format_volume(value):


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







def safe_float(

    value,

    default=0.0

):


    try:


        value = float(value)



        if np.isnan(value):

            return default



        return value



    except Exception:


        return default





# ============================================================
# BASIC DATA CLEANING
# ============================================================


def clean_market_data(

    dataframe

):


    if dataframe is None:


        return pd.DataFrame()



    if dataframe.empty:


        return pd.DataFrame()



    data = dataframe.copy()



    # Remove duplicate dates

    if "Date" in data.columns:


        data = data.drop_duplicates(

            subset=["Date"]

        )


        data = data.sort_values(

            "Date"

        )



    # Replace invalid values

    data = data.replace(

        [

            np.inf,

            -np.inf

        ],

        np.nan

    )



    # Numeric conversion

    numeric_columns = [

        "Open",

        "High",

        "Low",

        "Close",

        "Volume"

    ]



    for column in numeric_columns:


        if column in data.columns:


            data[column] = pd.to_numeric(

                data[column],

                errors="coerce"

            )



    if "Close" in data.columns:


        data = data.dropna(

            subset=["Close"]

        )



    data = data.ffill()



    data = data.bfill()



    return data





# ============================================================
# VALIDATION SYSTEM
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



    if dataframe["Close"].isna().all():

        return False



    return True
    # ============================================================
# DATA_PROVIDER.PY PART 2/6
# TECHNICAL INDICATOR ENGINE
# ============================================================


# ============================================================
# MOVING AVERAGE FUNCTIONS
# ============================================================


def calculate_ema(

    series,

    period

):


    return (

        series

        .ewm(

            span=period,

            adjust=False

        )

        .mean()

    )





# ============================================================
# RSI CALCULATION
# ============================================================


def calculate_rsi(

    close,

    period=14

):


    delta = close.diff()



    gain = delta.clip(

        lower=0

    )



    loss = -delta.clip(

        upper=0

    )



    avg_gain = (

        gain

        .rolling(

            period,

            min_periods=1

        )

        .mean()

    )



    avg_loss = (

        loss

        .rolling(

            period,

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



    rsi = (

        100 -

        (

            100 /

            (1 + rs)

        )

    )



    return rsi.fillna(50)







# ============================================================
# MACD CALCULATION
# ============================================================


def calculate_macd(

    close

):


    ema12 = calculate_ema(

        close,

        12

    )



    ema26 = calculate_ema(

        close,

        26

    )



    macd = (

        ema12 -

        ema26

    )



    signal = (

        macd

        .ewm(

            span=9,

            adjust=False

        )

        .mean()

    )



    histogram = (

        macd -

        signal

    )



    return (

        macd,

        signal,

        histogram

    )







# ============================================================
# BOLLINGER BAND CALCULATION
# ============================================================


def calculate_bollinger_bands(

    close,

    period=20

):


    middle = (

        close

        .rolling(

            period,

            min_periods=1

        )

        .mean()

    )



    std = (

        close

        .rolling(

            period,

            min_periods=1

        )

        .std()

    )



    upper = (

        middle +

        (

            std * 2

        )

    )



    lower = (

        middle -

        (

            std * 2

        )

    )



    bandwidth = (

        upper -

        lower

    ) / middle



    return (

        upper,

        middle,

        lower,

        bandwidth

    )







# ============================================================
# ATR VOLATILITY CALCULATION
# ============================================================


def calculate_atr(

    dataframe,

    period=14

):


    high = dataframe["High"]

    low = dataframe["Low"]

    close = dataframe["Close"]



    previous_close = close.shift(1)



    true_range = pd.concat(

        [

            high - low,

            abs(high - previous_close),

            abs(low - previous_close)

        ],

        axis=1

    ).max(

        axis=1

    )



    atr = (

        true_range

        .rolling(

            period,

            min_periods=1

        )

        .mean()

    )



    return atr







# ============================================================
# MAIN INDICATOR PIPELINE
# ============================================================


def add_indicators(

    dataframe

):


    if dataframe is None:


        return pd.DataFrame()



    if dataframe.empty:


        return dataframe



    data = dataframe.copy()



    if "Close" not in data.columns:


        return data





    # ========================================================
    # RETURNS
    # ========================================================


    data["Return"] = (

        data["Close"]

        .pct_change()

        .fillna(0)

    )



    data["Log_Return"] = np.log(

        data["Close"] /

        data["Close"].shift(1)

    )



    data["Log_Return"] = (

        data["Log_Return"]

        .replace(

            [

                np.inf,

                -np.inf

            ],

            np.nan

        )

        .fillna(0)

    )







    # ========================================================
    # MOVING AVERAGES
    # ========================================================


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



    data["SMA200"] = (

        data["Close"]

        .rolling(

            200,

            min_periods=20

        )

        .mean()

    )



    data["EMA12"] = calculate_ema(

        data["Close"],

        12

    )



    data["EMA26"] = calculate_ema(

        data["Close"],

        26

    )







    # ========================================================
    # RSI
    # ========================================================


    data["RSI"] = calculate_rsi(

        data["Close"]

    )







    # ========================================================
    # MACD
    # ========================================================


    (

        data["MACD"],

        data["MACD_Signal"],

        data["MACD_Hist"]

    ) = calculate_macd(

        data["Close"]

    )







    # ========================================================
    # BOLLINGER BANDS
    # ========================================================


    (

        data["BB_Upper"],

        data["BB_Middle"],

        data["BB_Lower"],

        data["BB_Width"]

    ) = calculate_bollinger_bands(

        data["Close"]

    )







    # ========================================================
    # VOLATILITY
    # ========================================================


    data["Volatility"] = (

        data["Log_Return"]

        .rolling(

            20,

            min_periods=5

        )

        .std()

    )



    data["Volatility"] = (

        data["Volatility"]

        .fillna(

            data["Log_Return"].std()

        )

        .fillna(0)

    )







    # ========================================================
    # ATR
    # ========================================================


    if (

        "High" in data.columns

        and

        "Low" in data.columns

    ):


        data["ATR"] = calculate_atr(

            data

        )


    else:


        data["ATR"] = 0







    # ========================================================
    # MOMENTUM
    # ========================================================


    data["Momentum_20"] = (

        data["Close"]

        /

        data["Close"].shift(20)

        -

        1

    )



    data["Momentum_60"] = (

        data["Close"]

        /

        data["Close"].shift(60)

        -

        1

    )



    data["Momentum_20"] = (

        data["Momentum_20"]

        .replace(

            [

                np.inf,

                -np.inf

            ],

            np.nan

        )

        .fillna(0)

    )



    data["Momentum_60"] = (

        data["Momentum_60"]

        .replace(

            [

                np.inf,

                -np.inf

            ],

            np.nan

        )

        .fillna(0)

    )







    # ========================================================
    # VOLUME FEATURES
    # ========================================================


    if "Volume" in data.columns:


        data["Volume_Change"] = (

            data["Volume"]

            .pct_change()

        )



        data["Volume_Average_20"] = (

            data["Volume"]

            .rolling(

                20,

                min_periods=1

            )

            .mean()

        )



        data["Volume_Ratio"] = (

            data["Volume"]

            /

            data["Volume_Average_20"]

        )



    else:


        data["Volume_Change"] = 0

        data["Volume_Average_20"] = 0

        data["Volume_Ratio"] = 0





    # Clean remaining values

    data = data.replace(

        [

            np.inf,

            -np.inf

        ],

        np.nan

    )



    data = data.fillna(0)



    return data
    # ============================================================
# DATA_PROVIDER.PY PART 3/6
# ADVANCED MARKET FEATURES + QUANTUM MODEL PREPARATION
# ============================================================



# ============================================================
# MARKET REGIME DETECTION
# ============================================================


def calculate_market_regime(

    dataframe

):


    data = dataframe.copy()



    if data.empty:


        return data





    # ========================================================
    # TREND COMPONENT
    # ========================================================


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



    if "SMA200" in data.columns:


        trend_score += np.where(

            data["Close"] > data["SMA200"],

            1,

            -1

        )





    # ========================================================
    # MOMENTUM COMPONENT
    # ========================================================


    momentum_score = np.zeros(

        len(data)

    )



    momentum_score += np.where(

        data["Momentum_20"] > 0,

        1,

        -1

    )



    momentum_score += np.where(

        data["Momentum_60"] > 0,

        1,

        -1

    )





    # ========================================================
    # MACD COMPONENT
    # ========================================================


    macd_score = np.where(

        data["MACD"] >

        data["MACD_Signal"],

        1,

        -1

    )







    # ========================================================
    # COMBINED MARKET SCORE
    # ========================================================


    data["Trend_Score"] = (

        trend_score /

        3

    )



    data["Momentum_Score"] = (

        momentum_score /

        2

    )



    data["MACD_Score"] = macd_score





    data["Market_Strength"] = (

        (

            data["Trend_Score"] *

            0.45

        )

        +

        (

            data["Momentum_Score"] *

            0.35

        )

        +

        (

            data["MACD_Score"] *

            0.20

        )

    )



    data["Market_Strength"] = (

        (

            data["Market_Strength"]

            + 1

        )

        /

        2

    ) * 100







    # ========================================================
    # MARKET REGIME LABEL
    # ========================================================


    data["Market_Regime"] = "Neutral"



    data.loc[

        data["Market_Strength"] >= 65,

        "Market_Regime"

    ] = "Bullish"



    data.loc[

        data["Market_Strength"] <= 35,

        "Market_Regime"

    ] = "Bearish"







    return data







# ============================================================
# VOLATILITY REGIME
# ============================================================


def add_volatility_regime(

    dataframe

):


    data = dataframe.copy()



    if data.empty:


        return data





    volatility_average = (

        data["Volatility"]

        .rolling(

            60,

            min_periods=10

        )

        .mean()

    )



    data["Volatility_Regime"] = (

        data["Volatility"]

        /

        volatility_average

    )



    data["Volatility_Regime"] = (

        data["Volatility_Regime"]

        .replace(

            [

                np.inf,

                -np.inf

            ],

            np.nan

        )

        .fillna(1)

    )







    data["High_Volatility"] = np.where(

        data["Volatility_Regime"] > 1.5,

        1,

        0

    )



    return data







# ============================================================
# RISK FEATURES
# ============================================================


def add_risk_features(

    dataframe

):


    data = dataframe.copy()



    if data.empty:


        return data





    # Rolling downside deviation


    negative_returns = data["Return"].copy()



    negative_returns[

        negative_returns > 0

    ] = 0



    data["Downside_Volatility"] = (

        negative_returns

        .rolling(

            30,

            min_periods=5

        )

        .std()

    )





    # Maximum drawdown


    rolling_high = (

        data["Close"]

        .cummax()

    )



    drawdown = (

        data["Close"]

        /

        rolling_high

        -

        1

    )



    data["Drawdown"] = drawdown





    data["Max_Drawdown"] = (

        drawdown

        .rolling(

            252,

            min_periods=20

        )

        .min()

    )





    return data







# ============================================================
# ADVANCED FEATURE PIPELINE
# ============================================================


def add_advanced_features(

    dataframe

):


    if dataframe is None:


        return pd.DataFrame()



    if dataframe.empty:


        return dataframe



    data = dataframe.copy()



    try:




        # Trend distance


        data["SMA20_Distance"] = (

            data["Close"]

            -

            data["SMA20"]

        )

        /

        data["SMA20"]



        data["SMA50_Distance"] = (

            data["Close"]

            -

            data["SMA50"]

        )

        /

        data["SMA50"]







        # Run advanced systems


        data = calculate_market_regime(

            data

        )



        data = add_volatility_regime(

            data

        )



        data = add_risk_features(

            data

        )







        # ====================================================
        # QUANTUM FEATURE VECTOR
        # ====================================================


        data["Quantum_Feature_Score"] = (

            (

                data["Market_Strength"]

                *

                0.35

            )

            +

            (

                data["RSI"]

                /

                100

                *

                20

            )

            +

            (

                data["Momentum_20"]

                *

                20

            )

            -

            (

                data["Volatility"]

                *

                100

                *

                25

            )

        )



        data["Quantum_Feature_Score"] = (

            data["Quantum_Feature_Score"]

            .clip(

                0,

                100

            )

        )







        # Future AI integration fields


        data["News_Sentiment"] = 0



        data["Analyst_Score"] = 50







        return data





    except Exception as error:


        print(

            "Advanced feature error:",

            error

        )


        return data







# ============================================================
# BENCHMARK DATA PREPARATION
# ============================================================


@st.cache_data(

    ttl=900,

    max_entries=20

)

def get_market_benchmark(

    ticker="SPY"

):


    try:


        data = get_stock_data(

            ticker

        )


        return data



    except Exception:


        return pd.DataFrame()







# ============================================================
# FEATURE EXTRACTION FOR QUANTUM ENGINE
# ============================================================


def get_quantum_features(

    dataframe

):


    if dataframe is None:


        return {}



    if dataframe.empty:


        return {}





    latest = dataframe.iloc[-1]





    features = {



        "price":

        float(

            latest["Close"]

        ),



        "volatility":

        float(

            latest.get(

                "Volatility",

                0

            )

        ),



        "momentum":

        float(

            latest.get(

                "Momentum_20",

                0

            )

        ),



        "market_strength":

        float(

            latest.get(

                "Market_Strength",

                50

            )

        ),



        "rsi":

        float(

            latest.get(

                "RSI",

                50

            )

        ),



        "macd":

        float(

            latest.get(

                "MACD",

                0

            )

        ),



        "sentiment":

        float(

            latest.get(

                "News_Sentiment",

                0

            )

        )



    }



    return features
    # ============================================================
# DATA_PROVIDER.PY PART 4/6
# HISTORICAL DATA ENGINE + LIVE DATA SYSTEM
# ============================================================



# ============================================================
# HISTORICAL MARKET DATA LOADER
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



    url = (

        "https://query1.finance.yahoo.com/"

        f"v8/finance/chart/{ticker}"

        "?range=5y&interval=1d"

    )



    try:


        json_data = yahoo_request(

            url

        )



        if json_data is None:


            saved = load_saved_data(

                ticker

            )


            if saved.empty:


                return pd.DataFrame()



            saved = clean_market_data(

                saved

            )


            saved = add_indicators(

                saved

            )


            saved = add_advanced_features(

                saved

            )


            return saved





        result = (

            json_data

            .get(

                "chart",

                {}

            )

            .get(

                "result",

                []

            )

        )



        if not result:


            return pd.DataFrame()



        result = result[0]



        timestamps = result.get(

            "timestamp",

            []

        )



        indicators = result.get(

            "indicators",

            {}

        )



        quote = (

            indicators

            .get(

                "quote",

                [{}]

            )[0]

        )



        adjclose = (

            indicators

            .get(

                "adjclose",

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



                "Open":

                quote.get(

                    "open",

                    []

                ),



                "High":

                quote.get(

                    "high",

                    []

                ),



                "Low":

                quote.get(

                    "low",

                    []

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

                ),



                "Adjusted_Close":

                adjclose.get(

                    "adjclose",

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



        saved = load_saved_data(

            ticker

        )



        if saved.empty:


            return pd.DataFrame()



        saved = clean_market_data(

            saved

        )


        saved = add_indicators(

            saved

        )


        saved = add_advanced_features(

            saved

        )



        return saved







# ============================================================
# LIVE PRICE ENGINE
# ============================================================


@st.cache_data(

    ttl=15,

    max_entries=250

)

def get_live_price(

    ticker

):


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


        data = yahoo_request(

            url

        )



        if not data:


            return None





        result = (

            data

            .get(

                "chart",

                {}

            )

            .get(

                "result",

                []

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



        previous = meta.get(

            "previousClose"

        )



        if price is None:


            return None





        price = float(

            price

        )





        if previous:


            previous = float(

                previous

            )



            change = (

                (

                    price -

                    previous

                )

                /

                previous

            ) * 100



        else:


            change = 0





        return {



            "price":

            price,



            "previous_close":

            previous,



            "change_percent":

            change,



            "currency":

            meta.get(

                "currency",

                "USD"

            ),



            "exchange":

            meta.get(

                "exchangeName",

                "Unknown"

            )



        }





    except Exception as error:


        print(

            "Live price error:",

            error

        )



        return None







# ============================================================
# COMPANY INFORMATION SYSTEM
# ============================================================


@st.cache_data(

    ttl=3600,

    max_entries=250

)

def get_company_info(

    ticker

):


    ticker = (

        ticker

        .upper()

        .strip()

    )



    url = (

        "https://query1.finance.yahoo.com/"

        f"v7/finance/quote?symbols={ticker}"

    )



    try:


        data = yahoo_request(

            url

        )



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



        if results:


            info = results[0]



            return {



                "name":

                info.get(

                    "longName",

                    info.get(

                        "shortName",

                        ticker

                    )

                ),



                "symbol":

                ticker,



                "exchange":

                info.get(

                    "fullExchangeName",

                    "Unknown"

                ),



                "currency":

                info.get(

                    "currency",

                    "USD"

                ),



                "type":

                info.get(

                    "quoteType",

                    "Unknown"

                )



            }



    except Exception as error:


        print(

            "Company lookup error:",

            error

        )







    fallback = {



        "AAPL":

        "Apple Inc.",



        "MSFT":

        "Microsoft Corporation",



        "NVDA":

        "NVIDIA Corporation",



        "GOOGL":

        "Alphabet Inc.",



        "AMZN":

        "Amazon Inc.",



        "META":

        "Meta Platforms Inc.",



        "TSLA":

        "Tesla Inc."

    }





    return {



        "name":

        fallback.get(

            ticker,

            ticker

        ),



        "symbol":

        ticker,



        "exchange":

        "Unknown",



        "currency":

        "USD",



        "type":

        "Unknown"

    }
    # ============================================================
# DATA_PROVIDER.PY PART 5/6
# SEARCH ENGINE + VALIDATION + CACHE SYSTEM
# ============================================================



# ============================================================
# STOCK SEARCH SYSTEM
# ============================================================


@st.cache_data(

    ttl=3600,

    max_entries=500

)

def search_stocks(

    query

):


    if query is None:


        return []



    query = (

        query

        .strip()

    )



    if len(query) < 1:


        return []





    url = (

        "https://query1.finance.yahoo.com/"

        f"v1/finance/search?q={query}"

    )



    try:


        data = yahoo_request(

            url

        )



        if not data:


            return []





        quotes = data.get(

            "quotes",

            []

        )



        results = []





        for item in quotes:



            symbol = item.get(

                "symbol"

            )



            name = (

                item.get(

                    "longname"

                )

                or

                item.get(

                    "shortname"

                )

            )



            quote_type = item.get(

                "quoteType",

                ""

            )





            if not symbol:


                continue





            priority = 0





            if quote_type == "EQUITY":


                priority += 10





            if quote_type == "ETF":


                priority += 5





            if symbol.upper() == query.upper():


                priority += 20





            results.append(

                {


                    "label":

                    f"{name or symbol} ({symbol})",



                    "symbol":

                    symbol,



                    "name":

                    name or symbol,



                    "priority":

                    priority



                }

            )







        results = sorted(

            results,

            key=lambda x:

            x["priority"],

            reverse=True

        )





        return results[:15]





    except Exception as error:


        print(

            "Search error:",

            error

        )



        return []







# ============================================================
# MARKET DATA VALIDATION
# ============================================================


def validate_market_data(

    dataframe

):


    if dataframe is None:


        return False





    if dataframe.empty:


        return False





    required = [

        "Close"

    ]





    for column in required:


        if column not in dataframe.columns:


            return False





    dataframe["Close"] = pd.to_numeric(

        dataframe["Close"],

        errors="coerce"

    )





    dataframe = dataframe.dropna(

        subset=[

            "Close"

        ]

    )





    if len(dataframe) < 20:


        return False





    return True







# ============================================================
# MARKET STATUS
# ============================================================


def get_market_status(

    live_data

):


    if live_data is None:


        return "Offline"



    return (

        "Live Data Connected"

    )







# ============================================================
# CACHE MANAGEMENT
# ============================================================


def clear_data_cache():


    try:


        st.cache_data.clear()



    except Exception as error:


        print(

            "Cache clear failed:",

            error

        )







# ============================================================
# SAFE NUMBER HANDLING
# ============================================================


def safe_float(

    value,

    default=0.0

):


    try:


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


    ticker = (

        ticker

        .upper()

        .strip()

    )



    live = get_live_price(

        ticker

    )



    historical = get_stock_data(

        ticker

    )





    latest_features = get_quantum_features(

        historical

    )







    return {



        "ticker":

        ticker,



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

        ),



        "market_regime":

        latest_features.get(

            "market_strength",

            None

        ),



        "quantum_score":

        latest_features.get(

            "market_strength",

            None

        )



    }







# ============================================================
# MODEL INPUT CHECK
# ============================================================


def validate_quantum_features(

    features

):


    required = [

        "price",

        "volatility",

        "momentum",

        "market_strength",

        "rsi"

    ]



    for item in required:


        if item not in features:


            return False





    return True







# ============================================================
# FINAL DATA PROVIDER HEALTH CHECK
# ============================================================


def provider_health_check():


    status = {



        "Yahoo_API":

        False,



        "Cache":

        True,



        "Indicators":

        True,



        "Quantum_Features":

        True



    }



    try:


        test = get_live_price(

            "AAPL"

        )



        if test:


            status["Yahoo_API"] = True





    except Exception:


        pass





    return status
    # ============================================================
# DATA_PROVIDER.PY PART 6/6
# PRODUCTION HELPERS + EXPORT SYSTEM + TESTING
# ============================================================



# ============================================================
# EXPORT MARKET DATA
# ============================================================


def export_market_data(

    ticker,

    dataframe

):


    try:


        if dataframe is None:


            return False





        if dataframe.empty:


            return False





        filename = (

            f"{ticker.upper()}_market_data.csv"

        )



        dataframe.to_csv(

            filename,

            index=False

        )



        return True





    except Exception as error:


        print(

            "Export failed:",

            error

        )


        return False







# ============================================================
# FEATURE SUMMARY
# ============================================================


def get_feature_summary(

    ticker

):


    data = get_stock_data(

        ticker

    )



    if data.empty:


        return {}





    latest = data.iloc[-1]





    return {



        "Ticker":

        ticker.upper(),



        "Price":

        safe_float(

            latest.get(

                "Close",

                0

            )

        ),



        "RSI":

        safe_float(

            latest.get(

                "RSI",

                50

            )

        ),



        "Momentum":

        safe_float(

            latest.get(

                "Momentum_20",

                0

            )

        ),



        "Volatility":

        safe_float(

            latest.get(

                "Volatility",

                0

            )

        ),



        "Market Strength":

        safe_float(

            latest.get(

                "Market_Strength",

                50

            )

        ),



        "Regime":

        latest.get(

            "Market_Regime",

            "Neutral"

        )



    }







# ============================================================
# MODEL COMPATIBILITY CHECK
# ============================================================


def quantum_model_ready(

    dataframe

):


    if dataframe is None:


        return False





    if dataframe.empty:


        return False





    required_features = [

        "Close",

        "Return",

        "Volatility",

        "Momentum_20",

        "Market_Strength",

        "RSI"

    ]





    for feature in required_features:


        if feature not in dataframe.columns:


            return False





    return True







# ============================================================
# APPLICATION STARTUP CHECK
# ============================================================


def initialize_provider():


    folders = [

        DATA_FOLDER

    ]



    for folder in folders:


        if not os.path.exists(folder):


            os.makedirs(

                folder

            )



    return True







# ============================================================
# DATA PROVIDER VERSION
# ============================================================


DATA_PROVIDER_VERSION = (

    "Quantum Equity Data Engine v2.0"

)







# ============================================================
# FINAL DEBUG INFORMATION
# ============================================================


def debug_information():



    return {



        "version":

        DATA_PROVIDER_VERSION,



        "data_folder":

        DATA_FOLDER,



        "cache":

        "Enabled",



        "features":

        [

            "Returns",

            "Log Returns",

            "SMA",

            "RSI",

            "MACD",

            "Momentum",

            "Volatility",

            "Drawdown",

            "Market Regime",

            "Quantum Feature Vector"

        ]



    }







# ============================================================
# TESTING
# ============================================================


if __name__ == "__main__":


    print(

        "Starting Quantum Equity Data Provider Test"

    )



    initialize_provider()



    test_symbol = "AAPL"





    print(

        "\nFetching historical data..."

    )



    data = get_stock_data(

        test_symbol

    )



    if data.empty:


        print(

            "No data returned"

        )


    else:


        print(

            data.tail()

        )





    print(

        "\nFetching live price..."

    )



    live = get_live_price(

        test_symbol

    )



    print(

        live

    )





    print(

        "\nFeature Summary"

    )



    print(

        get_feature_summary(

            test_symbol

        )

    )





    print(

        "\nProvider Health"

    )



    print(

        provider_health_check()

    )





# ============================================================
# END OF DATA_PROVIDER.PY
# ============================================================
