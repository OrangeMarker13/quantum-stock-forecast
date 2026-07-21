# ============================================================
# DATA_PROVIDER.PY
# Quantum Equity Research Terminal
# Production Data Infrastructure
# PART 1/6
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

REQUEST_TIMEOUT = 15
MAX_RETRIES = 3


if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)


YAHOO_HEADERS = {
    "User-Agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}


# ============================================================
# SAFE REQUEST ENGINE
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


            print(
                "Yahoo request failed:",
                response.status_code
            )


        except Exception as error:

            print(
                "Yahoo request error:",
                error
            )


        time.sleep(1)


    return None



# ============================================================
# DATA STORAGE
# ============================================================

def save_stock_data(ticker, dataframe):

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
            "Save error:",
            error
        )



def load_saved_data(ticker):

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
            "Load error:",
            error
        )

        return pd.DataFrame()



# ============================================================
# FORMATTING HELPERS
# ============================================================

def format_price(value):

    try:

        return f"${float(value):,.2f}"

    except Exception:

        return "N/A"



def format_percent(value):

    try:

        return f"{float(value):+.2f}%"

    except Exception:

        return "N/A"



def format_volume(value):

    try:

        value = float(value)


        if value >= 1_000_000_000:

            return f"{value/1_000_000_000:.2f}B"


        if value >= 1_000_000:

            return f"{value/1_000_000:.2f}M"


        if value >= 1_000:

            return f"{value/1_000:.2f}K"


        return str(int(value))


    except Exception:

        return "N/A"



def safe_float(value, default=0.0):

    try:

        value = float(value)


        if np.isnan(value):

            return default


        return value


    except Exception:

        return default



# ============================================================
# CLEAN MARKET DATA
# ============================================================

def clean_market_data(dataframe):

    if dataframe is None:

        return pd.DataFrame()


    if dataframe.empty:

        return pd.DataFrame()



    data = dataframe.copy()



    if "Date" in data.columns:

        data = data.drop_duplicates(
            subset=["Date"]
        )


        data = data.sort_values(
            "Date"
        )



    data = data.replace(
        [
            np.inf,
            -np.inf
        ],
        np.nan
    )


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
            subset=[
                "Close"
            ]
        )



    data = data.ffill()
    data = data.bfill()


    return data



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
# DATA_PROVIDER.PY PART 2/6
# TECHNICAL INDICATOR ENGINE
# ============================================================


def calculate_ema(series, period):
    return (
        series
        .ewm(
            span=period,
            adjust=False
        )
        .mean()
    )


def calculate_rsi(close, period=14):

    delta = close.diff()

    gain = delta.clip(lower=0)

    loss = -delta.clip(upper=0)

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



def calculate_macd(close):

    ema12 = calculate_ema(
        close,
        12
    )

    ema26 = calculate_ema(
        close,
        26
    )

    macd = ema12 - ema26

    signal = (
        macd
        .ewm(
            span=9,
            adjust=False
        )
        .mean()
    )

    histogram = macd - signal

    return (
        macd,
        signal,
        histogram
    )



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
        .fillna(0)
    )

    upper = middle + (std * 2)

    lower = middle - (std * 2)

    width = (
        (upper - lower) /
        middle.replace(
            0,
            np.nan
        )
    )

    return (
        upper.fillna(0),
        middle.fillna(0),
        lower.fillna(0),
        width.fillna(0)
    )



def calculate_atr(
    dataframe,
    period=14
):

    if not all(
        column in dataframe.columns
        for column in [
            "High",
            "Low",
            "Close"
        ]
    ):
        return pd.Series(
            0,
            index=dataframe.index
        )


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
    ).max(axis=1)


    return (
        true_range
        .rolling(
            period,
            min_periods=1
        )
        .mean()
        .fillna(0)
    )



def add_indicators(dataframe):

    if dataframe is None:
        return pd.DataFrame()


    if dataframe.empty:
        return dataframe


    data = dataframe.copy()


    if "Close" not in data.columns:
        return data



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



    data["RSI"] = calculate_rsi(
        data["Close"]
    )



    (
        data["MACD"],
        data["MACD_Signal"],
        data["MACD_Hist"]
    ) = calculate_macd(
        data["Close"]
    )



    (
        data["BB_Upper"],
        data["BB_Middle"],
        data["BB_Lower"],
        data["BB_Width"]
    ) = calculate_bollinger_bands(
        data["Close"]
    )



    data["Volatility"] = (
        data["Log_Return"]
        .rolling(
            20,
            min_periods=5
        )
        .std()
        .fillna(0)
    )



    data["ATR"] = calculate_atr(
        data
    )



    data["Momentum_20"] = (
        data["Close"] /
        data["Close"].shift(20)
        - 1
    ).replace(
        [
            np.inf,
            -np.inf
        ],
        np.nan
    ).fillna(0)



    data["Momentum_60"] = (
        data["Close"] /
        data["Close"].shift(60)
        - 1
    ).replace(
        [
            np.inf,
            -np.inf
        ],
        np.nan
    ).fillna(0)



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
            .fillna(0)
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
            data["Volume"] /
            data["Volume_Average_20"].replace(
                0,
                np.nan
            )
        ).fillna(0)


    else:

        data["Volume_Change"] = 0

        data["Volume_Average_20"] = 0

        data["Volume_Ratio"] = 0



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


def calculate_market_regime(dataframe):

    data = dataframe.copy()

    if data.empty:
        return data


    trend_score = np.zeros(len(data))


    if "SMA20" in data.columns:

        trend_score += np.where(
            data["Close"] > data["SMA20"],
            1,
            -1
        )


    if "SMA50" in data.columns:

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


    momentum_score = np.zeros(len(data))


    if "Momentum_20" in data.columns:

        momentum_score += np.where(
            data["Momentum_20"] > 0,
            1,
            -1
        )


    if "Momentum_60" in data.columns:

        momentum_score += np.where(
            data["Momentum_60"] > 0,
            1,
            -1
        )


    macd_score = np.zeros(len(data))


    if (
        "MACD" in data.columns
        and
        "MACD_Signal" in data.columns
    ):

        macd_score = np.where(
            data["MACD"] > data["MACD_Signal"],
            1,
            -1
        )


    data["Trend_Score"] = trend_score / 3

    data["Momentum_Score"] = momentum_score / 2

    data["MACD_Score"] = macd_score


    data["Market_Strength"] = (

        (data["Trend_Score"] * 0.45)

        +

        (data["Momentum_Score"] * 0.35)

        +

        (data["MACD_Score"] * 0.20)

    )


    data["Market_Strength"] = (

        (

            data["Market_Strength"]

            +

            1

        )

        /

        2

    ) * 100



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


def add_volatility_regime(dataframe):


    data = dataframe.copy()


    if data.empty:

        return data



    average_volatility = (

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

        average_volatility

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


def add_risk_features(dataframe):


    data = dataframe.copy()


    if data.empty:

        return data



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


    rolling_high = (

        data["Close"]

        .cummax()

    )


    data["Drawdown"] = (

        data["Close"]

        /

        rolling_high

        -

        1

    )


    data["Max_Drawdown"] = (

        data["Drawdown"]

        .rolling(
            252,
            min_periods=20
        )

        .min()

    )


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
# ADVANCED FEATURE PIPELINE
# ============================================================


def add_advanced_features(dataframe):


    if dataframe is None:

        return pd.DataFrame()



    if dataframe.empty:

        return dataframe



    data = dataframe.copy()



    try:


        # Trend distance

        if "SMA20" in data.columns:

            data["SMA20_Distance"] = (

                (

                    data["Close"]

                    -

                    data["SMA20"]

                )

                /

                data["SMA20"]

            )


        if "SMA50" in data.columns:

            data["SMA50_Distance"] = (

                (

                    data["Close"]

                    -

                    data["SMA50"]

                )

                /

                data["SMA50"]

            )



        data = calculate_market_regime(data)


        data = add_volatility_regime(data)


        data = add_risk_features(data)



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


        # Placeholder inputs for future models

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
# QUANTUM MODEL FEATURE EXTRACTION
# ============================================================


def get_quantum_features(dataframe):


    if dataframe is None:

        return {}



    if dataframe.empty:

        return {}



    latest = dataframe.iloc[-1]



    return {


        "price":

        safe_float(
            latest.get(
                "Close",
                0
            )
        ),



        "volatility":

        safe_float(
            latest.get(
                "Volatility",
                0
            )
        ),



        "momentum":

        safe_float(
            latest.get(
                "Momentum_20",
                0
            )
        ),



        "market_strength":

        safe_float(
            latest.get(
                "Market_Strength",
                50
            )
        ),



        "rsi":

        safe_float(
            latest.get(
                "RSI",
                50
            )
        ),



        "macd":

        safe_float(
            latest.get(
                "MACD",
                0
            )
        ),



        "sentiment":

        safe_float(
            latest.get(
                "News_Sentiment",
                0
            )
        )


    }
    # ============================================================
# DATA_PROVIDER.PY PART 4/6
# HISTORICAL DATA ENGINE + LIVE DATA SYSTEM
# ============================================================


# ============================================================
# YAHOO FINANCE DATA FETCHER
# ============================================================


def fetch_yahoo_chart(ticker, period="5y"):


    ticker = ticker.upper().strip()


    urls = [

        (
            "https://query1.finance.yahoo.com/"
            f"v8/finance/chart/{ticker}"
            f"?range={period}&interval=1d"
        ),

        (
            "https://query2.finance.yahoo.com/"
            f"v8/finance/chart/{ticker}"
            f"?range={period}&interval=1d"
        )

    ]


    for url in urls:


        data = yahoo_request(url)


        if data is not None:


            try:

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


                if result:

                    return result[0]


            except Exception:

                pass



    return None





# ============================================================
# HISTORICAL MARKET DATA LOADER
# ============================================================


@st.cache_data(

    ttl=900,

    max_entries=100

)

def get_stock_data(ticker):


    ticker = ticker.upper().strip()



    chart = fetch_yahoo_chart(

        ticker

    )



    if chart is None:


        print(

            "Using local cache for",

            ticker

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





    try:


        timestamps = chart.get(

            "timestamp",

            []

        )



        quote = (

            chart

            .get(

                "indicators",

                {}

            )

            .get(

                "quote",

                [{}]

            )[0]

        )



        adjusted = (

            chart

            .get(

                "indicators",

                {}

            )

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

                adjusted.get(

                    "adjclose",

                    []

                )


            }


        )



        dataframe = clean_market_data(

            dataframe

        )



        if not validate_market_data(

            dataframe

        ):


            return pd.DataFrame()



        dataframe = add_indicators(

            dataframe

        )


        dataframe = add_advanced_features(

            dataframe

        )



        save_stock_data(

            ticker,

            dataframe

        )



        return dataframe



    except Exception as error:


        print(

            "Historical loader error:",

            error

        )


        return pd.DataFrame()





# ============================================================
# LIVE PRICE SYSTEM
# ============================================================


@st.cache_data(
    ttl=15,
    max_entries=250
)
def get_live_price(ticker):

    ticker = ticker.upper().strip()

    chart = fetch_yahoo_chart(
        ticker,
        period="5d"
    )

    if chart is None:
        return None

    try:

        meta = chart.get(
            "meta",
            {}
        )

        price = meta.get(
            "regularMarketPrice"
        )

        previous = meta.get(
            "previousClose"
        )


        quote = (
            chart
            .get(
                "indicators",
                {}
            )
            .get(
                "quote",
                [{}]
            )[0]
        )


        closes = quote.get(
            "close",
            []
        )


        closes = [
            x for x in closes
            if x is not None
        ]


        if price is None and closes:

            price = closes[-1]


        if previous is None and len(closes) >= 2:

            previous = closes[-2]


        if price is None:

            return None


        price = float(price)


        if previous:

            previous = float(previous)

            change = (
                (price - previous)
                /
                previous
            ) * 100

        else:

            change = 0



        return {

            "price": price,

            "previous_close": previous,

            "change_percent": change,

            "currency": meta.get(
                "currency",
                "USD"
            ),

            "exchange": meta.get(
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
# COMPANY INFORMATION
# ============================================================


@st.cache_data(

    ttl=3600,

    max_entries=250

)

def get_company_info(ticker):


    ticker = ticker.upper().strip()



    known = {


        "AAPL":

        "Apple Inc.",


        "MSFT":

        "Microsoft Corporation",


        "NVDA":

        "NVIDIA Corporation",


        "GOOGL":

        "Alphabet Inc.",


        "AMZN":

        "Amazon.com Inc.",


        "META":

        "Meta Platforms Inc.",


        "TSLA":

        "Tesla Inc."


    }



    return {


        "name":

        known.get(

            ticker,

            ticker

        ),


        "symbol":

        ticker,


        "exchange":

        "Unknown",


        "currency":

        "USD"


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

def search_stocks(query):


    if not query:


        return []



    query = query.strip()



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



        if data is None:


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


            if not symbol:


                continue



            name = (

                item.get(

                    "longname"

                )

                or

                item.get(

                    "shortname"

                )

                or

                symbol

            )



            quote_type = item.get(

                "quoteType",

                ""

            )



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

                    f"{name} ({symbol})",


                    "symbol":

                    symbol,


                    "name":

                    name,


                    "priority":

                    priority


                }

            )



        results.sort(

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


def validate_market_data(dataframe):


    if dataframe is None:


        return False



    if dataframe.empty:


        return False



    if "Close" not in dataframe.columns:


        return False



    data = dataframe.copy()



    data["Close"] = pd.to_numeric(

        data["Close"],

        errors="coerce"

    )



    data = data.dropna(

        subset=[

            "Close"

        ]

    )



    if len(data) < 20:


        return False



    if data["Close"].nunique() <= 1:


        return False



    return True







# ============================================================
# MARKET STATUS
# ============================================================


def get_market_status(live_data):


    if live_data is None:


        return "Offline"



    return "Live Data Connected"







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
# SAFE NUMBER HANDLING
# ============================================================


def safe_float(value, default=0.0):


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


def get_market_summary(ticker):


    ticker = ticker.upper().strip()



    live = get_live_price(

        ticker

    )



    historical = get_stock_data(

        ticker

    )



    features = get_quantum_features(

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



        "market_strength":

        features.get(

            "market_strength",

            0

        ),



        "quantum_score":

        features.get(

            "market_strength",

            0

        )


    }








# ============================================================
# QUANTUM FEATURE VALIDATION
# ============================================================


def validate_quantum_features(features):


    if not features:


        return False



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
# PROVIDER HEALTH CHECK
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



    except Exception as error:


        print(

            "Health check error:",

            error

        )



    return status





# ============================================================
# END PART 5
# ============================================================
# ============================================================
# DATA_PROVIDER.PY PART 6/6
# PRODUCTION HELPERS + EXPORT SYSTEM + TESTING
# ============================================================


# ============================================================
# EXPORT MARKET DATA
# ============================================================


def export_market_data(ticker, dataframe):


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

            "Export error:",

            error

        )


        return False






# ============================================================
# FEATURE SUMMARY
# ============================================================


def get_feature_summary(ticker):


    dataframe = get_stock_data(

        ticker

    )



    if dataframe.empty:


        return {}



    latest = dataframe.iloc[-1]



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



        "Market Regime":

        latest.get(

            "Market_Regime",

            "Neutral"

        )


    }








# ============================================================
# QUANTUM MODEL COMPATIBILITY CHECK
# ============================================================


def quantum_model_ready(dataframe):


    if dataframe is None:


        return False



    if dataframe.empty:


        return False



    required = [


        "Close",

        "Return",

        "Volatility",

        "Momentum_20",

        "Market_Strength",

        "RSI"


    ]



    for feature in required:


        if feature not in dataframe.columns:


            return False



    return True








# ============================================================
# PROVIDER INITIALIZATION
# ============================================================


def initialize_provider():


    try:


        if not os.path.exists(DATA_FOLDER):


            os.makedirs(

                DATA_FOLDER

            )



        return True



    except Exception as error:


        print(

            "Initialization error:",

            error

        )


        return False








# ============================================================
# VERSION INFORMATION
# ============================================================


DATA_PROVIDER_VERSION = (

    "Quantum Equity Data Engine v2.1"

)








# ============================================================
# DEBUG INFORMATION
# ============================================================


def debug_information():


    return {


        "version":

        DATA_PROVIDER_VERSION,



        "data_folder":

        DATA_FOLDER,



        "cache":

        "Streamlit cache enabled",



        "systems":

        [


            "Yahoo Data Connector",

            "Local CSV Backup",

            "Technical Indicators",

            "Market Regime Detection",

            "Risk Engine",

            "Quantum Feature Vector"


        ]


    }








# ============================================================
# FULL PROVIDER TEST
# ============================================================


def run_provider_test():


    initialize_provider()



    ticker = "AAPL"



    output = {}



    try:


        data = get_stock_data(

            ticker

        )



        output["historical_loaded"] = (

            not data.empty

        )



        output["rows"] = len(

            data

        )



        output["quantum_ready"] = quantum_model_ready(

            data

        )



        output["features"] = get_feature_summary(

            ticker

        )



        output["health"] = provider_health_check()



    except Exception as error:


        output["error"] = str(error)



    return output








# ============================================================
# LOCAL TESTING
# ============================================================


if __name__ == "__main__":


    print(

        "Starting Quantum Data Provider Test"

    )



    results = run_provider_test()



    for key, value in results.items():


        print(

            "\n",

            key,

            ":",

            value

        )






# ============================================================
# END DATA_PROVIDER.PY
# ============================================================
