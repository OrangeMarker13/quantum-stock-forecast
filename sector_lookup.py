# ============================================================
# sector_lookup.py
# Maps a stock ticker to a representative sector ETF ticker,
# used only to fetch a real macro/sector-tilt data series for
# the joint quantum forecast engine (quantum_joint_engine.py).
#
# This is intentionally a small, explicit table rather than a
# dynamic sector-classification lookup, so it's obvious exactly
# what proxy is being used and why. SPY is always used as the
# market-wide proxy; the sector ETF below is averaged with SPY.
# ============================================================

SECTOR_ETF_MAP = {
    # Technology
    "AAPL": "XLK", "MSFT": "XLK", "NVDA": "XLK", "GOOGL": "XLK",
    "META": "XLK", "AVGO": "XLK", "ORCL": "XLK", "CRM": "XLK",
    "ADBE": "XLK", "AMD": "XLK", "INTC": "XLK", "CSCO": "XLK",

    # Consumer Discretionary
    "AMZN": "XLY", "TSLA": "XLY", "HD": "XLY", "MCD": "XLY",
    "NKE": "XLY", "SBUX": "XLY",

    # Communication Services
    "NFLX": "XLC", "DIS": "XLC", "CMCSA": "XLC", "T": "XLC",
    "VZ": "XLC",

    # Financials
    "JPM": "XLF", "BAC": "XLF", "WFC": "XLF", "GS": "XLF",
    "MS": "XLF", "V": "XLF", "MA": "XLF",

    # Healthcare
    "JNJ": "XLV", "UNH": "XLV", "PFE": "XLV", "MRK": "XLV",
    "ABBV": "XLV", "LLY": "XLV",

    # Energy
    "XOM": "XLE", "CVX": "XLE", "COP": "XLE",

    # Industrials
    "BA": "XLI", "CAT": "XLI", "GE": "XLI", "UPS": "XLI",

    # Consumer Staples
    "PG": "XLP", "KO": "XLP", "PEP": "XLP", "WMT": "XLP", "COST": "XLP",

    # Utilities
    "NEE": "XLU", "DUK": "XLU", "SO": "XLU",

    # Real Estate
    "AMT": "XLRE", "PLD": "XLRE",

    # Materials
    "LIN": "XLB", "SHW": "XLB",
}

DEFAULT_SECTOR_ETF = "SPY"  # if ticker isn't in the map, don't
                             # fabricate a sector guess; fall back
                             # to SPY alone (handled upstream by
                             # combine_macro_proxy's single-source
                             # averaging logic degrading gracefully)


def get_sector_etf(ticker):
    """
    Return the sector ETF ticker for a given stock, or None if
    unknown. Returning None (rather than a guessed default) lets
    the caller decide to run in SPY-only macro mode instead of
    silently mixing in an unrelated sector.
    """

    ticker = ticker.upper().strip()

    return SECTOR_ETF_MAP.get(ticker)
