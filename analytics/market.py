import yfinance as yf
import pandas as pd
from functools import lru_cache
from typing import List, Dict

# -----------------------------------------
# Configuration
# -----------------------------------------

DEFAULT_SYMBOLS = ["AAPL", "MSFT", "SPY"]
DEFAULT_PERIOD = "3mo"

# -----------------------------------------
# Helpers
# -----------------------------------------

def _clean_dataframe(df: pd.DataFrame) -> pd.DataFrame | None:
    """
    Normalize yfinance output to a clean OHLC DataFrame.
    Returns None if data is unusable.
    """
    if df is None or df.empty:
        return None

    # Handle possible multi-index columns
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    required_cols = {"Open", "High", "Low", "Close"}
    if not required_cols.issubset(df.columns):
        return None

    df = df.copy()
    df = df.dropna(subset=["Close"])

    return df if len(df) >= 5 else None


# -----------------------------------------
# Cached Market Fetch
# -----------------------------------------

@lru_cache(maxsize=32)
def _fetch_single_symbol(symbol: str, period: str) -> pd.DataFrame | None:
    """
    Fetch data for a single symbol with caching.
    """
    try:
        df = yf.download(
            symbol,
            period=period,
            progress=False,
            auto_adjust=False,
            threads=False,
        )
        return _clean_dataframe(df)

    except Exception as e:
        print(f"[Market] Failed to fetch {symbol}: {e}")
        return None


# -----------------------------------------
# Public API
# -----------------------------------------

def fetch_market_data(
    symbols: List[str] | None = None,
    period: str = DEFAULT_PERIOD
) -> Dict[str, pd.DataFrame]:
    """
    Fetch market data for multiple symbols.
    Always returns a dict (symbol -> DataFrame).
    Invalid symbols are skipped safely.
    """
    symbols = symbols or DEFAULT_SYMBOLS

    results: Dict[str, pd.DataFrame] = {}

    for symbol in symbols:
        df = _fetch_single_symbol(symbol.upper(), period)
        if df is not None:
            results[symbol.upper()] = df

    return results
