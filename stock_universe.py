"""A bounded liquid-stock universe for unattended market-session forecasts."""

import json
import os
from pathlib import Path


DEFAULT_UNIVERSE = """
AAPL MSFT NVDA AMZN GOOGL GOOG META TSLA AVGO BRK-B JPM V WMT XOM MA UNH
LLY COST ORCL NFLX HD PG JNJ ABBV BAC KO CRM CVX MRK AMD PEP TMO LIN
ACN MCD CSCO WFC ABT DHR DIS QCOM TXN PM IBM GE CAT AMGN VZ INTU NOW
ISRG AMAT BKNG GS SPGI BLK ADP GILD SYK DE TJX LMT MDLZ SCHW PLD CCI
MO SO DUK NEE LOW UPS BA HON RTX COP SLB OXY FDX SBUX NKE TGT CMCSA
""".split()


def get_universe() -> list[str]:
    """Use a local custom list when supplied, otherwise a liquid default list."""
    configured = Path(__file__).with_name("stock_universe.json")
    if configured.exists():
        try:
            payload = json.loads(configured.read_text(encoding="utf-8"))
            symbols = payload.get("tickers", payload) if isinstance(payload, dict) else payload
            if isinstance(symbols, list):
                cleaned = [str(symbol).upper().strip() for symbol in symbols]
                cleaned = [symbol for symbol in cleaned if symbol.replace("-", "").replace(".", "").isalnum()]
                if cleaned:
                    return list(dict.fromkeys(cleaned))
        except (OSError, json.JSONDecodeError):
            pass
    return list(dict.fromkeys(DEFAULT_UNIVERSE))


def max_tickers() -> int:
    """Allow safe deployment tuning without one run overwhelming data sources."""
    try:
        requested = int(os.getenv("AUTONOMOUS_MAX_TICKERS", "75"))
    except ValueError:
        requested = 75
    return max(1, min(requested, len(get_universe())))
