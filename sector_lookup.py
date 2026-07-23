# ============================================================
# SECTOR_LOOKUP.PY
# Sector Lookup Mapping
# ============================================================
SECTOR_ETF_MAP = {
    "AAPL": "XLK", "MSFT": "XLK", "NVDA": "XLK", "GOOGL": "XLK",
    "META": "XLK", "AVGO": "XLK", "ORCL": "XLK", "CRM": "XLK",
    "ADBE": "XLK", "AMD": "XLK", "INTC": "XLK", "CSCO": "XLK",
    "AMZN": "XLY", "TSLA": "XLY", "HD": "XLY", "MCD": "XLY",
    "NKE": "XLY", "SBUX": "XLY",
    "NFLX": "XLC", "DIS": "XLC", "CMCSA": "XLC", "T": "XLC", "VZ": "XLC",
    "JPM": "XLF", "BAC": "XLF", "WFC": "XLF", "GS": "XLF", "MS": "XLF", "V": "XLF", "MA": "XLF",
    "JNJ": "XLV", "UNH": "XLV", "PFE": "XLV", "MRK": "XLV", "ABBV": "XLV", "LLY": "XLV",
    "XOM": "XLE", "CVX": "XLE", "COP": "XLE",
    "BA": "XLI", "CAT": "XLI", "GE": "XLI", "UPS": "XLI",
    "PG": "XLP", "KO": "XLP", "PEP": "XLP", "WMT": "XLP", "COST": "XLP",
    "NEE": "XLU", "DUK": "XLU", "SO": "XLU",
    "AMT": "XLRE", "PLD": "XLRE",
    "LIN": "XLB", "SHW": "XLB"
}

def get_sector_etf(ticker):
    return SECTOR_ETF_MAP.get(ticker.upper().strip())
