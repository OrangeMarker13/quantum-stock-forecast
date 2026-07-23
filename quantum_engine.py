# ============================================================
# QUANTUM_ENGINE.PY
# Classical Auxiliary Math Backend for Joint Multi-Factor QFT Stage
# ============================================================
import numpy as np

def calculate_market_state(close_series, external_features=None):
    if len(close_series) < 20:
        return 0.0, {"technical": 100.0, "macro": 0.0, "global": 0.0, "sector": 0.0, "sentiment": 0.0}, 0.0
    sma_20 = close_series.rolling(20).mean().iloc[-1]
    current_price = close_series.iloc[-1]
    tech_signal = np.clip((current_price - sma_20) / (sma_20 + 1e-9) * 10, -1.0, 1.0)
    
    weights = {"technical": 40.0, "macro": 20.0, "global": 10.0, "sector": 15.0, "sentiment": 15.0}
    market_state = tech_signal * 0.7
    if external_features:
        market_state += external_features.get("macro_score", 0.0) * 0.3
    return np.clip(market_state, -1.0, 1.0), weights, tech_signal

def calculate_expected_return(returns_series, market_state, days):
    mean_daily = returns_series.mean() if len(returns_series) > 0 else 0.0002
    daily_vol = returns_series.std() if len(returns_series) > 0 else 0.01
    return (mean_daily * days) + (market_state * daily_vol * np.sqrt(days))

def calculate_confidence(price_marginal, bins_per_factor, annual_volatility, market_state):
    pm = np.array(price_marginal)
    pm = pm / (pm.sum() + 1e-9)
    entropy = -np.sum(pm * np.log2(pm + 1e-9))
    max_entropy = np.log2(len(pm))
    entropy_factor = 1.0 - (entropy / (max_entropy + 1e-9))
    return float(np.clip((entropy_factor * 60.0) + (max(0.0, 1.0 - annual_volatility) * 30.0) + (abs(market_state) * 10.0), 0.0, 100.0))

def calculate_risk(price_marginal, return_grid, annual_volatility):
    pm = np.array(price_marginal)
    pm = pm / (pm.sum() + 1e-9)
    downside_mask = return_grid < 0
    if not np.any(downside_mask):
        downside_risk = 0.0
    else:
        downside_risk = np.sqrt(np.sum((pm[downside_mask] / (pm[downside_mask].sum() + 1e-9)) * (return_grid[downside_mask] ** 2)))
    return float(np.clip((downside_risk * 50.0) + (annual_volatility * 50.0), 0.0, 10.0)), float(downside_risk)
