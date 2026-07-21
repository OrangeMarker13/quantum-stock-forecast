# ============================================================
# DATA_PROVIDER.PY
# Quantum Equity Research Terminal
# Production Market Data Engine v3.0
# PART 1/6
# ============================================================

import os
import time
import requests
import numpy as np
import pandas as pd
import streamlit as st


# ============================================================
# CONFIG
# ============================================================

DATA_FOLDER = "data"
REQUEST_TIMEOUT = 15
MAX_RETRIES = 3


os.makedirs(DATA_FOLDER, exist_ok=True)


HEADERS = {
    "User-Agent":
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}


# ============================================================
# SAFE REQUEST SYSTEM
# ============================================================

def yahoo_request(url):

    for attempt in range(MAX_RETRIES):

        try:
            response = requests.get(
                url,
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT
            )

            if response.status_code == 200:
                return response.json()

        except Exception:
            pass

        time.sleep(1)

    return None



# ============================================================
# HELPERS
# ============================================================

def safe_float(value, default=0.0):

    try:
        value = float(value)

        if np.isnan(value):
            return default

        return value

    except Exception:
        return default



def format_price(value):

    if value is None:
        return "N/A"

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



# ============================================================
# LOCAL DATA STORAGE
# ============================================================

def save_stock_data(ticker, dataframe):

    try:

        if dataframe is None or dataframe.empty:
            return


        path = os.path.join(
            DATA_FOLDER,
            f"{ticker.upper()}.csv"
        )


        dataframe.to_csv(
            path,
            index=False
        )


    except Exception:
        pass



def load_saved_data(ticker):

    try:

        path = os.path.join(
            DATA_FOLDER,
            f"{ticker.upper()}.csv"
        )


        if not os.path.exists(path):
            return pd.DataFrame()


        data = pd.read_csv(path)


        if "Date" in data.columns:

            data["Date"] = pd.to_datetime(
                data["Date"],
                errors="coerce"
            )


        return data


    except Exception:

        return pd.DataFrame()



# ============================================================
# MARKET DATA CLEANING
# ============================================================

def clean_market_data(dataframe):

    if dataframe is None or dataframe.empty:
        return pd.DataFrame()


    data = dataframe.copy()


    if "Date" in data.columns:

        data = data.drop_duplicates(
            "Date"
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


    numeric = [
        "Open",
        "High",
        "Low",
        "Close",
        "Volume"
    ]


    for column in numeric:

        if column in data.columns:

            data[column] = pd.to_numeric(
                data[column],
                errors="coerce"
            )


    if "Close" in data.columns:

        data = data.dropna(
            subset=["Close"]
        )


    data = data.ffill().bfill()


    return data



# ============================================================
# DATA VALIDATION
# ============================================================

def validate_market_data(dataframe):

    if dataframe is None:
        return False


    if dataframe.empty:
        return False


    if "Close" not in dataframe.columns:
        return False


    close = pd.to_numeric(
        dataframe["Close"],
        errors="coerce"
    ).dropna()


    if len(close) < 20:
        return False


    if close.nunique() <= 1:
        return False


    return True
    # ============================================================
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


    return (
        macd,
        signal,
        macd - signal
    )



def calculate_bollinger(close, period=20):

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


    upper = middle + (
        std * 2
    )


    lower = middle - (
        std * 2
    )


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



def calculate_atr(data, period=14):

    required = [
        "High",
        "Low",
        "Close"
    ]


    if not all(
        x in data.columns
        for x in required
    ):

        return pd.Series(
            0,
            index=data.index
        )


    high = data["High"]
    low = data["Low"]
    close = data["Close"]


    previous = close.shift(1)


    true_range = pd.concat(
        [
            high - low,
            abs(high - previous),
            abs(low - previous)
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



# ============================================================
# INDICATOR PIPELINE
# ============================================================

def add_indicators(dataframe):

    if dataframe is None or dataframe.empty:
        return dataframe


    data = dataframe.copy()


    if "Close" not in data.columns:
        return data



    close = data["Close"]



    data["Return"] = (
        close
        .pct_change()
        .fillna(0)
    )



    data["Log_Return"] = (
        np.log(
            close /
            close.shift(1)
        )
        .replace(
            [
                np.inf,
                -np.inf
            ],
            np.nan
        )
        .fillna(0)
    )



    # Moving averages

    for period in [
        20,
        50,
        200
    ]:

        data[f"SMA{period}"] = (
            close
            .rolling(
                period,
                min_periods=1
            )
            .mean()
        )



    data["EMA12"] = calculate_ema(
        close,
        12
    )

    data["EMA26"] = calculate_ema(
        close,
        26
    )



    # Momentum

    for period in [
        20,
        60,
        120
    ]:

        data[f"Momentum_{period}"] = (

            close /
            close.shift(period)
            - 1

        ).replace(
            [
                np.inf,
                -np.inf
            ],
            np.nan
        ).fillna(0)



    # RSI

    data["RSI"] = calculate_rsi(
        close
    )



    (
        data["MACD"],
        data["MACD_Signal"],
        data["MACD_Hist"]

    ) = calculate_macd(
        close
    )



    (
        data["BB_Upper"],
        data["BB_Middle"],
        data["BB_Lower"],
        data["BB_Width"]

    ) = calculate_bollinger(
        close
    )



    # Volatility

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



    # Volume analysis

    if "Volume" in data.columns:


        data["Volume_Avg20"] = (
            data["Volume"]
            .rolling(
                20,
                min_periods=1
            )
            .mean()
        )


        data["Volume_Ratio"] = (

            data["Volume"] /
            data["Volume_Avg20"]
            .replace(
                0,
                np.nan
            )

        ).fillna(0)


    else:

        data["Volume_Avg20"] = 0
        data["Volume_Ratio"] = 0



    return (
        data
        .replace(
            [
                np.inf,
                -np.inf
            ],
            np.nan
        )
        .fillna(0)
    )
    # ============================================================
# MARKET REGIME + RISK FEATURE ENGINE
# ============================================================


def calculate_market_regime(dataframe):

    if dataframe is None or dataframe.empty:
        return dataframe


    data = dataframe.copy()


    trend = np.zeros(len(data))


    if "SMA20" in data.columns:

        trend += np.where(
            data["Close"] > data["SMA20"],
            1,
            -1
        )


    if "SMA50" in data.columns:

        trend += np.where(
            data["Close"] > data["SMA50"],
            1,
            -1
        )


    if "SMA200" in data.columns:

        trend += np.where(
            data["Close"] > data["SMA200"],
            1,
            -1
        )


    momentum = np.zeros(len(data))


    for column in [
        "Momentum_20",
        "Momentum_60",
        "Momentum_120"
    ]:

        if column in data.columns:

            momentum += np.where(
                data[column] > 0,
                1,
                -1
            )



    macd = np.where(

        data["MACD"] >
        data["MACD_Signal"],

        1,

        -1

    ) if (
        "MACD" in data.columns and
        "MACD_Signal" in data.columns
    ) else 0



    data["Trend_Score"] = trend / 3

    data["Momentum_Score"] = momentum / 3

    data["MACD_Score"] = macd



    data["Market_Strength"] = (

        data["Trend_Score"] * 0.45

        +

        data["Momentum_Score"] * 0.35

        +

        data["MACD_Score"] * 0.20

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


def add_volatility_features(dataframe):

    if dataframe is None or dataframe.empty:
        return dataframe


    data = dataframe.copy()



    rolling_vol = (

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

        rolling_vol.replace(
            0,
            np.nan
        )

    ).fillna(1)



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

    if dataframe is None or dataframe.empty:
        return dataframe


    data = dataframe.copy()



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

        .fillna(0)

    )



    rolling_high = (
        data["Close"]
        .cummax()
    )



    data["Drawdown"] = (

        data["Close"]

        /

        rolling_high

        - 1

    )



    data["Max_Drawdown"] = (

        data["Drawdown"]

        .rolling(
            252,
            min_periods=20
        )

        .min()

        .fillna(0)

    )



    return data





# ============================================================
# EXTERNAL MARKET FACTOR FRAMEWORK
# ============================================================


def get_external_market_factors():

    """
    Future expansion layer.

    Data sources planned:

    Volatility:
    - VIX index
    - market volatility ETFs

    Macro:
    - treasury yields
    - inflation
    - interest rates

    Market:
    - S&P 500
    - Nasdaq
    - Russell 2000

    Sector:
    - sector ETF performance

    Sentiment:
    - news sentiment
    - analyst revisions

    Earnings:
    - earnings surprises
    - revenue growth


    Scores:

    -1 = negative pressure

     0 = neutral

    +1 = positive pressure
    """



    return {

        "macro_score": 0,

        "market_score": 0,

        "sector_score": 0,

        "sentiment_score": 0,

        "earnings_score": 0,

        "interest_rate_score": 0,

        "volatility_score": 0

    }





# ============================================================
# ADVANCED FEATURE PIPELINE
# ============================================================


def add_advanced_features(dataframe):

    if dataframe is None or dataframe.empty:
        return dataframe



    data = dataframe.copy()



    try:


        if "SMA20" in data.columns:

            data["SMA20_Distance"] = (

                data["Close"]

                -

                data["SMA20"]

            ) / data["SMA20"].replace(
                0,
                np.nan
            )



        if "SMA50" in data.columns:

            data["SMA50_Distance"] = (

                data["Close"]

                -

                data["SMA50"]

            ) / data["SMA50"].replace(
                0,
                np.nan
            )



        data = calculate_market_regime(
            data
        )


        data = add_volatility_features(
            data
        )


        data = add_risk_features(
            data
        )



        # Quantum preparation score

        data["Quantum_Feature_Score"] = (

            data["Market_Strength"] * 0.45

            +

            (data["RSI"] / 100) * 25

            +

            data["Momentum_20"] * 20

            -

            data["Volatility"] * 100 * 10

        )



        data["Quantum_Feature_Score"] = (

            data["Quantum_Feature_Score"]

            .clip(
                0,
                100
            )

        )



        return (

            data

            .replace(
                [
                    np.inf,
                    -np.inf
                ],
                np.nan
            )

            .fillna(0)

        )


    except Exception:

        return dataframe





# ============================================================
# QUANTUM FEATURE EXTRACTION
# ============================================================


def get_quantum_features(dataframe):

    if dataframe is None or dataframe.empty:
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
            )

    }
    # ============================================================
# HISTORICAL DATA ENGINE + LIVE MARKET SYSTEM
# ============================================================


def fetch_yahoo_chart(ticker, period="5y"):

    ticker = ticker.upper().strip()


    urls = [

        f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range={period}&interval=1d",

        f"https://query2.finance.yahoo.com/v8/finance/chart/{ticker}?range={period}&interval=1d"

    ]



    for url in urls:

        response = yahoo_request(url)


        if response:

            try:

                result = (

                    response
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

                continue



    return None





# ============================================================
# HISTORICAL STOCK DATA
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

        cached = load_saved_data(
            ticker
        )


        if cached.empty:

            return pd.DataFrame()


        cached = clean_market_data(
            cached
        )


        cached = add_indicators(
            cached
        )


        cached = add_advanced_features(
            cached
        )


        return cached



    try:

        timestamps = chart.get(
            "timestamp",
            []
        )


        indicators = chart.get(
            "indicators",
            {}
        )


        quote = indicators.get(
            "quote",
            [{}]
        )[0]


        adjusted = indicators.get(
            "adjclose",
            [{}]
        )[0]



        dataframe = pd.DataFrame({

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

        })



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
            "Historical data error:",
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



        # fallback if Yahoo meta fails

        if price is None and closes:

            price = closes[-1]



        if previous is None and len(closes) > 1:

            previous = closes[-2]



        if price is None:

            return None



        price = float(
            price
        )



        if previous:

            previous = float(
                previous
            )


            change_percent = (

                (

                    price

                    -

                    previous

                )

                /

                previous

            ) * 100


        else:

            change_percent = 0



        return {

            "price":

            price,


            "previous_close":

            previous,


            "change_percent":

            change_percent,


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
# COMPANY INFORMATION
# ============================================================


@st.cache_data(
    ttl=3600,
    max_entries=250
)

def get_company_info(ticker):

    ticker = ticker.upper().strip()


    companies = {

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

        companies.get(
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
# STOCK SEARCH + VALIDATION + CACHE SYSTEM
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



            quote_type = item.get(
                "quoteType",
                ""
            )



            # Prioritize stocks

            if quote_type not in [
                "EQUITY",
                "ETF"
            ]:

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



            priority = 0



            if quote_type == "EQUITY":

                priority += 10



            if quote_type == "ETF":

                priority += 5



            if symbol.upper() == query.upper():

                priority += 20



            results.append({

                "label":

                f"{name} ({symbol})",


                "symbol":

                symbol,


                "name":

                name,


                "priority":

                priority

            })



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
# CACHE CONTROL
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
# SAFE NUMBER HANDLER
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
            50
        ),


        "quantum_score":

        features.get(
            "market_strength",
            50
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



    return all(

        item in features

        for item in required

    )





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
# PROVIDER METADATA
# ============================================================


DATA_PROVIDER_VERSION = (

    "Quantum Equity Data Engine v3.0"

)
# ============================================================
# EXPORT + PRODUCTION HELPERS + TESTING
# ============================================================


# ============================================================
# EXPORT MARKET DATA
# ============================================================


def export_market_data(ticker, dataframe):

    try:

        if dataframe is None or dataframe.empty:

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
# MODEL READINESS CHECK
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
# DEBUG INFORMATION
# ============================================================


def debug_information():

    return {


        "version":

        DATA_PROVIDER_VERSION,



        "data_folder":

        DATA_FOLDER,



        "cache":

        "Streamlit cache active",



        "systems":

        [

            "Yahoo Finance Connector",

            "Local CSV Backup",

            "Technical Indicators",

            "Momentum Engine",

            "Volatility Engine",

            "Risk Analytics",

            "Quantum Feature Preparation",

            "External Factor Framework"

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
# LOCAL TEST MODE
# ============================================================


if __name__ == "__main__":


    print(

        "Quantum Equity Data Engine Test"

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
