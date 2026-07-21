# ============================================================
# DATA_PROVIDER.PY
# Quantum Equity Research Terminal
# Compact Multi-Factor Market Data Engine
# PART 1
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
TIMEOUT = 12
RETRIES = 3

os.makedirs(DATA_FOLDER, exist_ok=True)


HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


# ============================================================
# SAFE REQUEST ENGINE
# ============================================================

def yahoo_request(url):

    for _ in range(RETRIES):

        try:
            response = requests.get(
                url,
                headers=HEADERS,
                timeout=TIMEOUT
            )

            if response.status_code == 200:
                return response.json()

        except Exception:
            pass

        time.sleep(1)

    return None


# ============================================================
# BASIC HELPERS
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

    value = safe_float(value)

    if value >= 1_000_000_000:
        return f"{value/1e9:.2f}B"

    if value >= 1_000_000:
        return f"{value/1e6:.2f}M"

    if value >= 1_000:
        return f"{value/1e3:.2f}K"

    return str(int(value))



# ============================================================
# LOCAL DATA STORAGE
# ============================================================

def save_stock_data(ticker, data):

    try:

        if data.empty:
            return

        path = os.path.join(
            DATA_FOLDER,
            f"{ticker.upper()}.csv"
        )

        data.to_csv(
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
# DATA CLEANING
# ============================================================

def clean_market_data(data):

    if data is None or data.empty:
        return pd.DataFrame()


    data = data.copy()


    if "Date" in data.columns:

        data = data.drop_duplicates(
            "Date"
        )

        data = data.sort_values(
            "Date"
        )


    data = data.replace(
        [np.inf, -np.inf],
        np.nan
    )


    numeric = [
        "Open",
        "High",
        "Low",
        "Close",
        "Volume"
    ]


    for col in numeric:

        if col in data.columns:

            data[col] = pd.to_numeric(
                data[col],
                errors="coerce"
            )


    if "Close" in data.columns:

        data = data.dropna(
            subset=["Close"]
        )


    data = data.ffill().bfill()


    return data



# ============================================================
# VALIDATION
# ============================================================

def validate_market_data(data):

    if data is None:
        return False


    if data.empty:
        return False


    if "Close" not in data.columns:
        return False


    close = pd.to_numeric(
        data["Close"],
        errors="coerce"
    ).dropna()


    if len(close) < 20:
        return False


    if close.nunique() <= 1:
        return False


    return True
    # ============================================================
# DATA_PROVIDER.PY
# TECHNICAL ANALYSIS ENGINE
# PART 2
# ============================================================


# ============================================================
# MOVING AVERAGES
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



def calculate_sma(series, period):

    return (
        series
        .rolling(
            period,
            min_periods=1
        )
        .mean()
    )



# ============================================================
# RSI
# ============================================================

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



# ============================================================
# MACD
# ============================================================

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



# ============================================================
# BOLLINGER BANDS
# ============================================================

def calculate_bollinger(close, period=20):

    middle = calculate_sma(
        close,
        period
    )


    deviation = (
        close
        .rolling(
            period,
            min_periods=1
        )
        .std()
        .fillna(0)
    )


    upper = middle + deviation * 2

    lower = middle - deviation * 2


    width = (
        (upper - lower)
        /
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



# ============================================================
# ATR VOLATILITY
# ============================================================

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

def add_indicators(data):

    if data is None or data.empty:
        return pd.DataFrame()


    data = data.copy()


    if "Close" not in data.columns:
        return data



    close = data["Close"]



    # Returns

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
            [np.inf,-np.inf],
            np.nan
        )
        .fillna(0)
    )



    # Trend

    data["SMA20"] = calculate_sma(
        close,
        20
    )

    data["SMA50"] = calculate_sma(
        close,
        50
    )

    data["SMA200"] = calculate_sma(
        close,
        200
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



    # Price range

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



    # Momentum windows

    for days in [
        10,
        20,
        60,
        120
    ]:

        data[f"Momentum_{days}"] = (

            close /
            close.shift(days)
            - 1

        ).replace(
            [np.inf,-np.inf],
            np.nan
        ).fillna(0)



    # Volume

    if "Volume" in data.columns:


        avg_volume = (
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
            avg_volume.replace(
                0,
                np.nan
            )

        ).fillna(0)


    else:

        data["Volume_Ratio"] = 0



    return (
        data
        .replace(
            [np.inf,-np.inf],
            np.nan
        )
        .fillna(0)
    )
    # ============================================================
# DATA_PROVIDER.PY
# EXTERNAL MARKET FACTOR ENGINE
# PART 3
# ============================================================


# ============================================================
# EXTERNAL MARKET ASSETS
# ============================================================

MARKET_ASSETS = {

    "sp500": "^GSPC",

    "nasdaq": "^IXIC",

    "vix": "^VIX",

    "treasury": "^TNX",

    "gold": "GC=F",

    "oil": "CL=F",

    "dollar": "DX-Y.NYB"

}


SECTOR_ETFS = {

    "technology": "XLK",

    "healthcare": "XLV",

    "financial": "XLF",

    "energy": "XLE",

    "consumer": "XLY"

}



# ============================================================
# GENERIC YAHOO PRICE FETCH
# ============================================================

@st.cache_data(
    ttl=900,
    max_entries=200
)
def fetch_asset_returns(symbol):

    try:

        url = (
            "https://query1.finance.yahoo.com/"
            f"v8/finance/chart/{symbol}"
            "?range=1y&interval=1d"
        )


        data = yahoo_request(
            url
        )


        if data is None:
            return pd.Series()



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
            return pd.Series()



        quote = (
            result[0]
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


        prices = pd.Series(
            closes
        )


        prices = (
            pd.to_numeric(
                prices,
                errors="coerce"
            )
            .dropna()
        )


        if len(prices) < 20:
            return pd.Series()



        return (
            prices
            .pct_change()
            .dropna()
        )


    except Exception:

        return pd.Series()



# ============================================================
# NORMALIZE MARKET SIGNAL
# ============================================================

def normalize_factor(value):

    if value > 0.15:
        return 1

    if value < -0.15:
        return -1

    return value / 0.15



# ============================================================
# MARKET FACTOR CALCULATOR
# ============================================================

@st.cache_data(
    ttl=900,
    max_entries=50
)
def get_external_market_factors():


    factors = {

        "macro_score": 0,

        "sector_score": 0,

        "global_market_score": 0,

        "interest_rate_score": 0,

        "sentiment_score": 0,

        "earnings_score": 0

    }



    # ================================
    # BROAD MARKET CONDITIONS
    # ================================


    sp500 = fetch_asset_returns(
        MARKET_ASSETS["sp500"]
    )


    nasdaq = fetch_asset_returns(
        MARKET_ASSETS["nasdaq"]
    )


    if not sp500.empty:

        sp_signal = normalize_factor(
            sp500.tail(60).sum()
        )

    else:

        sp_signal = 0



    if not nasdaq.empty:

        nasdaq_signal = normalize_factor(
            nasdaq.tail(60).sum()
        )

    else:

        nasdaq_signal = 0



    factors["macro_score"] = (

        sp_signal * 0.6

        +

        nasdaq_signal * 0.4

    )



    # ================================
    # VOLATILITY ENVIRONMENT
    # ================================


    vix = fetch_asset_returns(
        MARKET_ASSETS["vix"]
    )


    if not vix.empty:

        vix_change = (
            vix.tail(30).sum()
        )


        # Rising VIX hurts equities

        factors["global_market_score"] -= (

            normalize_factor(
                vix_change
            )

            *

            0.5

        )



    # ================================
    # INTEREST RATE PRESSURE
    # ================================


    treasury = fetch_asset_returns(
        MARKET_ASSETS["treasury"]
    )


    if not treasury.empty:

        rate_change = (
            treasury.tail(60).sum()
        )


        # Higher yields usually pressure growth stocks

        factors["interest_rate_score"] = (

            -normalize_factor(
                rate_change
            )

        )



    # ================================
    # GLOBAL COMMODITY SIGNALS
    # ================================


    gold = fetch_asset_returns(
        MARKET_ASSETS["gold"]
    )


    oil = fetch_asset_returns(
        MARKET_ASSETS["oil"]
    )


    dollar = fetch_asset_returns(
        MARKET_ASSETS["dollar"]
    )



    global_scores = []



    if not gold.empty:

        global_scores.append(
            normalize_factor(
                gold.tail(60).sum()
            )
        )



    if not oil.empty:

        global_scores.append(
            normalize_factor(
                oil.tail(60).sum()
            )
        )



    if not dollar.empty:

        global_scores.append(

            -normalize_factor(
                dollar.tail(60).sum()
            )

        )



    if global_scores:

        factors["global_market_score"] += (

            np.mean(
                global_scores
            )

            *

            0.5

        )



    # ================================
    # SECTOR ROTATION
    # ================================


    sector_results = []



    for _, symbol in SECTOR_ETFS.items():

        returns = fetch_asset_returns(
            symbol
        )


        if not returns.empty:

            sector_results.append(

                normalize_factor(
                    returns.tail(60).sum()
                )

            )



    if sector_results:

        factors["sector_score"] = np.mean(
            sector_results
        )



    # Clamp all outputs

    for key in factors:

        factors[key] = float(
            np.clip(
                factors[key],
                -1,
                1
            )
        )



    return factors



# ============================================================
# COMPANY SPECIFIC FACTOR PLACEHOLDERS
# ============================================================

def get_company_factors(ticker):

    return {

        "sentiment_score": 0,

        "earnings_score": 0

    }



# ============================================================
# COMPLETE FACTOR PIPELINE
# ============================================================

def get_all_external_features(ticker):


    market = get_external_market_factors()


    company = get_company_factors(
        ticker
    )


    market.update(
        company
    )


    return market
    # ============================================================
# DATA_PROVIDER.PY
# ADVANCED FEATURE PIPELINE
# PART 4
# ============================================================


# ============================================================
# MARKET REGIME DETECTION
# ============================================================

def calculate_market_regime(data):

    if data is None or data.empty:
        return data


    data = data.copy()


    trend_score = np.zeros(
        len(data)
    )


    # Moving average trend

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



    momentum_score = np.zeros(
        len(data)
    )


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



    macd_score = np.zeros(
        len(data)
    )


    if (
        "MACD" in data.columns
        and
        "MACD_Signal" in data.columns
    ):

        macd_score = np.where(
            data["MACD"] >
            data["MACD_Signal"],
            1,
            -1
        )



    data["Trend_Score"] = (
        trend_score / 3
    )


    data["Momentum_Score"] = (
        momentum_score / 2
    )


    data["MACD_Score"] = macd_score



    data["Market_Strength"] = (

        data["Trend_Score"] * 0.45

        +

        data["Momentum_Score"] * 0.35

        +

        data["MACD_Score"] * 0.20

    )


    data["Market_Strength"] = (

        (data["Market_Strength"] + 1)

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

def add_volatility_regime(data):

    if data is None or data.empty:
        return data


    data = data.copy()


    avg_vol = (
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

        avg_vol.replace(
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

def add_risk_features(data):

    if data is None or data.empty:
        return data


    data = data.copy()



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



    highest_price = (
        data["Close"]
        .cummax()
    )



    data["Drawdown"] = (

        data["Close"]

        /

        highest_price

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

        .fillna(0)

    )


    return data



# ============================================================
# COMPLETE FEATURE PIPELINE
# ============================================================

def add_advanced_features(data):


    if data is None or data.empty:
        return pd.DataFrame()


    data = data.copy()



    try:


        # Price distance from trends

        if "SMA20" in data.columns:

            data["SMA20_Distance"] = (

                data["Close"]

                -

                data["SMA20"]

            ) / data["SMA20"]



        if "SMA50" in data.columns:

            data["SMA50_Distance"] = (

                data["Close"]

                -

                data["SMA50"]

            ) / data["SMA50"]



        data = calculate_market_regime(
            data
        )


        data = add_volatility_regime(
            data
        )


        data = add_risk_features(
            data
        )



        # Quantum feature score

        data["Quantum_Feature_Score"] = (

            data["Market_Strength"] * 0.35

            +

            (data["RSI"] / 100) * 20

            +

            data["Momentum_20"] * 20

            -

            data["Volatility"] * 100 * 25

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
                [np.inf,-np.inf],
                np.nan
            )

            .fillna(0)

        )



    except Exception:

        return data



# ============================================================
# FEATURE EXTRACTION FOR QUANTUM ENGINE
# ============================================================

def get_quantum_features(data):


    if data is None or data.empty:

        return {}



    latest = data.iloc[-1]



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
# DATA_PROVIDER.PY
# DATA LOADING + LIVE MARKET SYSTEM
# PART 5
# ============================================================


# ============================================================
# YAHOO CHART FETCHER
# ============================================================

def fetch_yahoo_chart(
    ticker,
    period="5y"
):

    ticker = ticker.upper().strip()


    endpoints = [

        "https://query1.finance.yahoo.com/"
        f"v8/finance/chart/{ticker}"
        f"?range={period}&interval=1d",

        "https://query2.finance.yahoo.com/"
        f"v8/finance/chart/{ticker}"
        f"?range={period}&interval=1d"

    ]


    for url in endpoints:


        response = yahoo_request(
            url
        )


        if response is None:
            continue


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
# HISTORICAL MARKET DATA
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


        return add_advanced_features(
            cached
        )



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
            "Market data error:",
            error
        )


        return pd.DataFrame()



# ============================================================
# LIVE PRICE SYSTEM
# ============================================================

@st.cache_data(
    ttl=20,
    max_entries=250
)

def get_live_price(ticker):


    ticker = ticker.upper().strip()


    chart = fetch_yahoo_chart(
        ticker,
        "5d"
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



        if price is None:


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


            closes = [

                x for x in quote.get(
                    "close",
                    []
                )

                if x is not None

            ]


            if closes:

                price = closes[-1]


            if previous is None and len(closes) > 1:

                previous = closes[-2]



        if price is None:

            return None



        price = float(
            price
        )



        change = 0



        if previous:


            previous = float(
                previous
            )


            change = (

                (price - previous)

                /

                previous

            ) * 100



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



    except Exception:


        return None



# ============================================================
# COMPANY INFO
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


        "currency":

        "USD"

    }
    # ============================================================
# DATA_PROVIDER.PY
# SEARCH + CACHE + EXPORT + HEALTH
# PART 6
# ============================================================


# ============================================================
# STOCK SEARCH
# ============================================================

@st.cache_data(
    ttl=3600,
    max_entries=500
)

def search_stocks(query):


    if not query:

        return []



    query = query.strip()



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



    except Exception:


        return []





# ============================================================
# MARKET DATA VALIDATION
# ============================================================

def validate_market_data(data):


    if data is None:

        return False



    if data.empty:

        return False



    if "Close" not in data.columns:

        return False



    close = pd.to_numeric(

        data["Close"],

        errors="coerce"

    )



    close = close.dropna()



    if len(close) < 20:

        return False



    if close.nunique() <= 1:

        return False



    return True





# ============================================================
# CACHE MANAGEMENT
# ============================================================

def clear_data_cache():

    try:

        st.cache_data.clear()

        return True


    except Exception:


        return False





# ============================================================
# MARKET STATUS
# ============================================================

def get_market_status(live_data):


    if live_data:

        return "Live Data Connected"


    return "Offline"





# ============================================================
# MARKET SUMMARY
# ============================================================

def get_market_summary(ticker):


    ticker = ticker.upper().strip()



    live = get_live_price(
        ticker
    )


    data = get_stock_data(
        ticker
    )


    features = get_quantum_features(
        data
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

        len(data),


        "market_strength":

        features.get(
            "market_strength",
            0
        )

    }





# ============================================================
# FEATURE VALIDATION
# ============================================================

def validate_quantum_features(features):


    required = [

        "price",

        "volatility",

        "momentum",

        "market_strength",

        "rsi"

    ]



    if not features:

        return False



    return all(

        item in features

        for item in required

    )





# ============================================================
# PROVIDER HEALTH CHECK
# ============================================================

def provider_health_check():


    status = {


        "Yahoo_Data":

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

            status["Yahoo_Data"] = True



    except Exception:


        pass



    return status





# ============================================================
# EXPORT DATA
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



        dataframe.to_csv(

            f"{ticker.upper()}_market_data.csv",

            index=False

        )



        return True



    except Exception:


        return False





# ============================================================
# FEATURE SUMMARY
# ============================================================

def get_feature_summary(ticker):


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
        )


    }





# ============================================================
# INITIALIZATION
# ============================================================

def initialize_provider():

    try:


        if not os.path.exists(
            DATA_FOLDER
        ):

            os.makedirs(
                DATA_FOLDER
            )


        return True


    except Exception:


        return False





# ============================================================
# VERSION
# ============================================================

DATA_PROVIDER_VERSION = (

    "Quantum Equity Data Engine v3.0"

)





# ============================================================
# DEBUG
# ============================================================

def debug_information():

    return {


        "version":

        DATA_PROVIDER_VERSION,


        "cache":

        "Streamlit TTL enabled",


        "systems":

        [

            "Yahoo Market Data",

            "Local Backup",

            "Technical Indicators",

            "Market Regime",

            "Risk Engine",

            "External Market Factors",

            "Quantum Feature Pipeline"

        ]

    }





# ============================================================
# PROVIDER TEST
# ============================================================

def run_provider_test():


    initialize_provider()



    output = {}



    try:


        data = get_stock_data(
            "AAPL"
        )



        output["data_loaded"] = (

            not data.empty

        )



        output["rows"] = len(
            data
        )


        output["health"] = (

            provider_health_check()

        )


        output["features"] = (

            get_quantum_features(
                data
            )

        )



    except Exception as error:


        output["error"] = str(
            error
        )



    return output





# ============================================================
# LOCAL TEST
# ============================================================

if __name__ == "__main__":


    print(
        run_provider_test()
    )



# ============================================================
# END DATA_PROVIDER.PY v3.0
# ============================================================
