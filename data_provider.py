# ============================================================
# DATA_PROVIDER.PY
# Production Market Data Engine v3.0
# ============================================================
import os
import time
import requests
import numpy as np
import pandas as pd
import streamlit as st

DATA_FOLDER = "data"
REQUEST_TIMEOUT = 15
MAX_RETRIES = 3
os.makedirs(DATA_FOLDER, exist_ok=True)
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

# A network search failure must not turn a recognizable company name (for
# example, "Apple") into the invalid ticker "APPLE" in the UI.  Yahoo search
# remains the primary source; this compact fallback covers the companies the
# app already presents as known assets.
LOCAL_COMPANY_SEARCH = {
    "apple": ("AAPL", "Apple Inc."),
    "microsoft": ("MSFT", "Microsoft Corporation"),
    "nvidia": ("NVDA", "NVIDIA Corporation"),
    "alphabet": ("GOOGL", "Alphabet Inc."),
    "google": ("GOOGL", "Alphabet Inc."),
    "amazon": ("AMZN", "Amazon.com Inc."),
    "meta": ("META", "Meta Platforms Inc."),
    "tesla": ("TSLA", "Tesla Inc."),
}

def yahoo_request(url):
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            if response.status_code == 200: return response.json()
        except: pass
        time.sleep(1)
    return None

def safe_float(value, default=0.0):
    try:
        val = float(value)
        return default if np.isnan(val) else val
    except: return default

def format_price(value):
    if value is None: return "N/A"
    try: return f"${float(value):,.2f}"
    except: return "N/A"

def format_percent(value):
    try: return f"{float(value):+.2f}%"
    except: return "N/A"

def format_volume(value):
    try:
        value = float(value)
        if value >= 1_000_000_000: return f"{value/1_000_000_000:.2f}B"
        if value >= 1_000_000: return f"{value/1_000_000:.2f}M"
        if value >= 1_000: return f"{value/1_000:.2f}K"
        return str(int(value))
    except: return "N/A"

def save_stock_data(ticker, dataframe):
    try:
        if dataframe is None or dataframe.empty: return
        path = os.path.join(DATA_FOLDER, f"{ticker.upper()}.csv")
        dataframe.to_csv(path, index=False)
    except: pass

def load_saved_data(ticker):
    try:
        path = os.path.join(DATA_FOLDER, f"{ticker.upper()}.csv")
        if not os.path.exists(path): return pd.DataFrame()
        data = pd.read_csv(path)
        if "Date" in data.columns:
            data["Date"] = pd.to_datetime(data["Date"], errors="coerce")
        return data
    except: return pd.DataFrame()

def clean_market_data(dataframe):
    if dataframe is None or dataframe.empty: return pd.DataFrame()
    data = dataframe.copy()
    if "Date" in data.columns:
        data = data.drop_duplicates("Date").sort_values("Date")
    data = data.replace([np.inf, -np.inf], np.nan)
    numeric = ["Open", "High", "Low", "Close", "Volume"]
    for column in numeric:
        if column in data.columns:
            data[column] = pd.to_numeric(data[column], errors="coerce")
    if "Close" in data.columns:
        data = data.dropna(subset=["Close"])
    return data.ffill().bfill()

def validate_market_data(dataframe):
    if dataframe is None or dataframe.empty or "Close" not in dataframe.columns: return False
    close = pd.to_numeric(dataframe["Close"], errors="coerce").dropna()
    return not (len(close) < 20 or close.nunique() <= 1)

def calculate_ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

def calculate_rsi(close, period=14):
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period, min_periods=1).mean()
    avg_loss = loss.rolling(period, min_periods=1).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return (100 - (100 / (1 + rs))).fillna(50)

def calculate_macd(close):
    ema12 = calculate_ema(close, 12)
    ema26 = calculate_ema(close, 26)
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd, signal, macd - signal

def calculate_bollinger(close, period=20):
    middle = close.rolling(period, min_periods=1).mean()
    std = close.rolling(period, min_periods=1).std().fillna(0)
    upper = middle + (std * 2)
    lower = middle - (std * 2)
    width = (upper - lower) / middle.replace(0, np.nan)
    return upper.fillna(0), middle.fillna(0), lower.fillna(0), width.fillna(0)

def calculate_atr(data, period=14):
    required = ["High", "Low", "Close"]
    if not all(x in data.columns for x in required): return pd.Series(0, index=data.index)
    high, low, close = data["High"], data["Low"], data["Close"]
    previous = close.shift(1)
    tr = pd.concat([high - low, abs(high - previous), abs(low - previous)], axis=1).max(axis=1)
    return tr.rolling(period, min_periods=1).mean().fillna(0)

def add_indicators(dataframe):
    if dataframe is None or dataframe.empty: return dataframe
    data = dataframe.copy()
    if "Close" not in data.columns: return data
    close = data["Close"]
    data["Return"] = close.pct_change().fillna(0)
    data["Log_Return"] = np.log(close / close.shift(1)).replace([np.inf, -np.inf], np.nan).fillna(0)
    for period in [20, 50, 200]:
        data[f"SMA{period}"] = close.rolling(period, min_periods=1).mean()
    data["EMA12"] = calculate_ema(close, 12)
    data["EMA26"] = calculate_ema(close, 26)
    for period in [20, 60, 120]:
        data[f"Momentum_{period}"] = (close / close.shift(period) - 1).replace([np.inf, -np.inf], np.nan).fillna(0)
    data["RSI"] = calculate_rsi(close)
    data["MACD"], data["MACD_Signal"], data["MACD_Hist"] = calculate_macd(close)
    data["BB_Upper"], data["BB_Middle"], data["BB_Lower"], data["BB_Width"] = calculate_bollinger(close)
    data["Volatility"] = data["Log_Return"].rolling(20, min_periods=5).std().fillna(0)
    data["ATR"] = calculate_atr(data)
    if "Volume" in data.columns:
        data["Volume_Avg20"] = data["Volume"].rolling(20, min_periods=1).mean()
        data["Volume_Ratio"] = (data["Volume"] / data["Volume_Avg20"].replace(0, np.nan)).fillna(0)
    else:
        data["Volume_Avg20"], data["Volume_Ratio"] = 0, 0
    return data.replace([np.inf, -np.inf], np.nan).fillna(0)

def calculate_market_regime(dataframe):
    if dataframe is None or dataframe.empty: return dataframe
    data = dataframe.copy()
    trend = np.zeros(len(data))
    if "SMA20" in data.columns: trend += np.where(data["Close"] > data["SMA20"], 1, -1)
    if "SMA50" in data.columns: trend += np.where(data["Close"] > data["SMA50"], 1, -1)
    if "SMA200" in data.columns: trend += np.where(data["Close"] > data["SMA200"], 1, -1)
    momentum = np.zeros(len(data))
    for col in ["Momentum_20", "Momentum_60", "Momentum_120"]:
        if col in data.columns: momentum += np.where(data[col] > 0, 1, -1)
    macd = np.where(data["MACD"] > data["MACD_Signal"], 1, -1) if ("MACD" in data.columns and "MACD_Signal" in data.columns) else 0
    data["Trend_Score"], data["Momentum_Score"], data["MACD_Score"] = trend / 3, momentum / 3, macd
    data["Market_Strength"] = (data["Trend_Score"] * 0.45 + data["Momentum_Score"] * 0.35 + data["MACD_Score"] * 0.20)
    data["Market_Strength"] = ((data["Market_Strength"] + 1) / 2) * 100
    data["Market_Regime"] = "Neutral"
    data.loc[data["Market_Strength"] >= 65, "Market_Regime"] = "Bullish"
    data.loc[data["Market_Strength"] <= 35, "Market_Regime"] = "Bearish"
    return data

def add_volatility_features(dataframe):
    if dataframe is None or dataframe.empty: return dataframe
    data = dataframe.copy()
    rolling_vol = data["Volatility"].rolling(60, min_periods=10).mean()
    data["Volatility_Regime"] = (data["Volatility"] / rolling_vol.replace(0, np.nan)).fillna(1)
    data["High_Volatility"] = np.where(data["Volatility_Regime"] > 1.5, 1, 0)
    return data

def add_risk_features(dataframe):
    if dataframe is None or dataframe.empty: return dataframe
    data = dataframe.copy()
    neg_ret = data["Return"].copy()
    neg_ret[neg_ret > 0] = 0
    data["Downside_Volatility"] = neg_ret.rolling(30, min_periods=5).std().fillna(0)
    rolling_high = data["Close"].cummax()
    data["Drawdown"] = (data["Close"] / rolling_high - 1)
    data["Max_Drawdown"] = data["Drawdown"].rolling(252, min_periods=20).min().fillna(0)
    return data

def add_advanced_features(dataframe):
    if dataframe is None or dataframe.empty: return dataframe
    data = dataframe.copy()
    try:
        if "SMA20" in data.columns: data["SMA20_Distance"] = (data["Close"] - data["SMA20"]) / data["SMA20"].replace(0, np.nan)
        if "SMA50" in data.columns: data["SMA50_Distance"] = (data["Close"] - data["SMA50"]) / data["SMA50"].replace(0, np.nan)
        data = calculate_market_regime(data)
        data = add_volatility_features(data)
        data = add_risk_features(data)
        data["Quantum_Feature_Score"] = (data["Market_Strength"] * 0.45 + (data["RSI"] / 100) * 25 + data["Momentum_20"] * 20 - data["Volatility"] * 100 * 10).clip(0, 100)
        return data.replace([np.inf, -np.inf], np.nan).fillna(0)
    except: return dataframe

def get_quantum_features(dataframe):
    if dataframe is None or dataframe.empty: return {}
    latest = dataframe.iloc[-1]
    return {
        "price": safe_float(latest.get("Close", 0)),
        "volatility": safe_float(latest.get("Volatility", 0)),
        "momentum": safe_float(latest.get("Momentum_20", 0)),
        "market_strength": safe_float(latest.get("Market_Strength", 50)),
        "rsi": safe_float(latest.get("RSI", 50)),
        "macd": safe_float(latest.get("MACD", 0))
    }

def fetch_yahoo_chart(ticker, period="5y"):
    ticker = ticker.upper().strip()
    urls = [f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range={period}&interval=1d",
            f"https://query2.finance.yahoo.com/v8/finance/chart/{ticker}?range={period}&interval=1d"]
    for url in urls:
        response = yahoo_request(url)
        if response:
            try:
                res = response.get("chart", {}).get("result", [])
                if res: return res[0]
            except: continue
    return None

def safe_build_dataframe(timestamps, quote, adjusted):
    length = len(timestamps)
    def get_column_data(source, key, default_val=np.nan):
        data = source.get(key, [])
        if not isinstance(data, list): data = []
        if len(data) < length: data = data + [default_val] * (length - len(data))
        elif len(data) > length: data = data[:length]
        return data
    df_data = {
        "Date": pd.to_datetime(timestamps, unit="s", errors="coerce"),
        "Open": get_column_data(quote, "open"),
        "High": get_column_data(quote, "high"),
        "Low": get_column_data(quote, "low"),
        "Close": get_column_data(quote, "close"),
        "Volume": get_column_data(quote, "volume"),
        "Adjusted_Close": get_column_data(adjusted, "adjclose", np.nan)
    }
    if all(pd.isna(x) for x in df_data["Adjusted_Close"]):
        df_data["Adjusted_Close"] = df_data["Close"]
    return pd.DataFrame(df_data)

@st.cache_data(ttl=900, max_entries=100)
def get_stock_data(ticker):
    ticker = ticker.upper().strip()
    chart = fetch_yahoo_chart(ticker)
    if chart is None:
        cached = load_saved_data(ticker)
        if cached.empty: return pd.DataFrame()
        cached = clean_market_data(cached)
        return add_advanced_features(add_indicators(cached))
    try:
        timestamps = chart.get("timestamp", [])
        quote = chart.get("indicators", {}).get("quote", [{}])[0]
        adjusted = chart.get("indicators", {}).get("adjclose", [{}])[0]
        dataframe = safe_build_dataframe(timestamps, quote, adjusted)
        dataframe = clean_market_data(dataframe)
        if not validate_market_data(dataframe): return pd.DataFrame()
        dataframe = add_advanced_features(add_indicators(dataframe))
        save_stock_data(ticker, dataframe)
        return dataframe
    except Exception as error:
        print("Historical data error:", error)
        return pd.DataFrame()

@st.cache_data(ttl=15, max_entries=250)
def get_live_price(ticker):
    ticker = ticker.upper().strip()
    chart = fetch_yahoo_chart(ticker, period="5d")
    if chart is None: return None
    try:
        meta = chart.get("meta", {})
        price, previous = meta.get("regularMarketPrice"), meta.get("previousClose")
        quote = chart.get("indicators", {}).get("quote", [{}])[0]
        closes = [x for x in quote.get("close", []) if x is not None]
        if price is None and closes: price = closes[-1]
        if previous is None and len(closes) > 1: previous = closes[-2]
        if price is None: return None
        price = float(price)
        change_percent = ((price - previous) / previous) * 100 if previous else 0
        return {
            "price": price, "previous_close": previous, "change_percent": change_percent,
            "currency": meta.get("currency", "USD"), "exchange": meta.get("exchangeName", "Unknown")
        }
    except Exception as error:
        print("Live price error:", error)
        return None

@st.cache_data(ttl=3600, max_entries=250)
def get_company_info(ticker):
    ticker = ticker.upper().strip()
    companies = {"AAPL": "Apple Inc.", "MSFT": "Microsoft Corporation", "NVDA": "NVIDIA Corporation",
                 "GOOGL": "Alphabet Inc.", "AMZN": "Amazon.com Inc.", "META": "Meta Platforms Inc.", "TSLA": "Tesla Inc."}
    return {"name": companies.get(ticker, ticker), "symbol": ticker, "exchange": "Unknown", "currency": "USD"}

@st.cache_data(ttl=3600, max_entries=500)
def search_stocks(query):
    if not query: return []
    query = query.strip()
    query_key = query.casefold()

    def local_matches():
        matches = []
        for company_key, (symbol, name) in LOCAL_COMPANY_SEARCH.items():
            if query_key in company_key or query_key in name.casefold() or query_key == symbol.casefold():
                matches.append({"label": f"{name} ({symbol})", "symbol": symbol, "name": name, "priority": 100})
        return matches

    url = f"https://query1.finance.yahoo.com/v1/finance/search?q={query}"
    try:
        data = yahoo_request(url)
        if data is None: return local_matches()
        quotes, results = data.get("quotes", []), []
        for item in quotes:
            symbol = item.get("symbol")
            if not symbol: continue
            quote_type = item.get("quoteType", "")
            if quote_type not in ["EQUITY", "ETF"]: continue
            name = item.get("longname") or item.get("shortname") or symbol
            priority = 0
            if quote_type == "EQUITY": priority += 10
            if quote_type == "ETF": priority += 5
            if symbol.upper() == query.upper(): priority += 20
            results.append({"label": f"{name} ({symbol})", "symbol": symbol, "name": name, "priority": priority})
        results.sort(key=lambda x: x["priority"], reverse=True)
        # Preserve useful local resolution if Yahoo's result set is empty or
        # omits a well-known company-name query.
        return (results or local_matches())[:15]
    except Exception as error:
        print("Search error:", error)
        return local_matches()

def clear_data_cache():
    try:
        st.cache_data.clear()
        return True
    except: return False

def provider_health_check():
    status = {"Yahoo_API": False, "Cache": True, "Indicators": True, "Quantum_Features": True}
    try:
        if get_live_price("AAPL"): status["Yahoo_API"] = True
    except: pass
    return status

DATA_PROVIDER_VERSION = "Quantum Equity Data Engine v3.0"
