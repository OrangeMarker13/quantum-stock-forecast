# ============================================================
# ANALYTICS.PY
# Quantum Equity Research Terminal - Market Analytics Engine
# ============================================================
import numpy as np
import pandas as pd

def clean_market_data(data):
    df = data.copy()
    numeric_columns = df.select_dtypes(include=np.number).columns
    df[numeric_columns] = df[numeric_columns].replace([np.inf, -np.inf], np.nan).fillna(0)
    return df

def add_features(data):
    df = clean_market_data(data)
    df["Return"] = df["Close"].pct_change().fillna(0)
    df["MA_7"] = df["Close"].rolling(7).mean()
    df["MA_30"] = df["Close"].rolling(30).mean()
    df["MA_90"] = df["Close"].rolling(90).mean()
    df["Volatility"] = df["Return"].rolling(30).std()
    df["Momentum_20"] = df["Close"] / df["Close"].shift(20) - 1
    
    delta = df["Close"].diff()
    gains = delta.clip(lower=0)
    losses = -delta.clip(upper=0)
    avg_gain = gains.rolling(14).mean()
    avg_loss = losses.rolling(14).mean()
    rs = avg_gain / (avg_loss + 1e-9)
    df["RSI"] = 100 - (100 / (1 + rs))
    
    df["Market_Strength"] = df["MA_30"] / (df["MA_90"] + 1e-9) * 50
    df["Market_Strength"] = np.clip(df["Market_Strength"], 0, 100)
    return df.replace([np.inf, -np.inf], np.nan).fillna(0)

def extract_inputs(data):
    row = data.iloc[-1]
    return {
        "price": float(row["Close"]),
        "volatility": float(row["Volatility"]),
        "momentum": float(row["Momentum_20"]),
        "market_strength": float(row["Market_Strength"]),
        "rsi": float(row["RSI"])
    }

def validate_inputs(data, inputs):
    required_columns = ["Close", "Return", "Volatility", "Momentum_20", "RSI", "Market_Strength"]
    required_inputs = ["price", "volatility", "momentum", "market_strength", "rsi"]
    return (
        not data.empty
        and all(col in data.columns for col in required_columns)
        and all(key in inputs for key in required_inputs)
    )

def calculate_metrics(history):
    if not history: return {}
    df = pd.DataFrame(history)
    completed = df[df["actual_price"].notna()]
    if completed.empty: return {"predictions": 0}
    completed["error_percent"] = (abs(completed["actual_price"] - completed["predicted_price"]) / completed["predicted_price"] * 100)
    return {
        "predictions": len(completed),
        "accuracy": max(0, 100 - completed["error_percent"].mean()),
        "average_error": completed["error_percent"].mean()
    }

def create_forecast_report(data):
    if not data: return pd.DataFrame()
    report = {
        "Starting Price": data.get("starting_price", 0),
        "Expected Price": data.get("expected_price", 0),
        "Volatility": data.get("volatility", 0),
        "Confidence": data.get("confidence_score", 0),
        "Risk Score": data.get("risk_score", 0),
        "Market Regime": data.get("market_regime", "Unknown"),
        "Upside Probability": data.get("upside_probability", 0),
        "Downside Probability": data.get("downside_probability", 0)
    }
    return pd.DataFrame({"Metric": list(report.keys()), "Value": list(report.values())})
