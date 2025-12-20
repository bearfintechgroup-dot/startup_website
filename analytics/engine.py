import pandas as pd
from typing import Dict

# ============================================================
# Configuration / Constants
# ============================================================
SHORT_MA_WINDOW = 10
LONG_MA_WINDOW = 30
TRADING_DAYS_PER_YEAR = 252

STRONG_TREND_THRESHOLD = 0.4  # percent


# ============================================================
# Helpers
# ============================================================
def _to_series(x):
    """
    Ensure we always work with a pandas Series.
    yfinance sometimes returns DataFrames for columns.
    """
    if isinstance(x, pd.DataFrame):
        return x.iloc[:, 0]
    return x


# ============================================================
# Core Analytics
# ============================================================
def analyze_asset(df: pd.DataFrame) -> Dict[str, float | str]:
    close = _to_series(df["Close"]).dropna()

    # Defensive guard
    if close.empty or len(close) < LONG_MA_WINDOW:
        return {}

    returns = close.pct_change()

    total_return = (close.iloc[-1] / close.iloc[0] - 1) * 100

    short_ma = close.rolling(window=SHORT_MA_WINDOW).mean()
    long_ma = close.rolling(window=LONG_MA_WINDOW).mean()

    short_last = float(short_ma.iloc[-1])
    long_last = float(long_ma.iloc[-1])

    trend = "Bullish" if short_last > long_last else "Bearish"

    # Trend strength = % distance between moving averages
    trend_strength = (
        ((short_last - long_last) / long_last) * 100
        if long_last != 0
        else 0.0
    )

    momentum = (
        float(close.iloc[-1] - close.iloc[-SHORT_MA_WINDOW])
        if len(close) >= SHORT_MA_WINDOW
        else 0.0
    )

    volatility = float(returns.std() * (TRADING_DAYS_PER_YEAR ** 0.5))

    # UI-friendly signal label
    if trend == "Bullish" and trend_strength > STRONG_TREND_THRESHOLD:
        signal = "Strong Bullish"
    elif trend == "Bearish" and trend_strength < -STRONG_TREND_THRESHOLD:
        signal = "Strong Bearish"
    else:
        signal = "Neutral"

    return {
        "price": round(float(close.iloc[-1]), 2),
        "total_return": round(float(total_return), 2),
        "trend": trend,
        "trend_strength": round(float(trend_strength), 2),
        "signal": signal,
        "momentum": round(float(momentum), 2),
        "volatility": round(float(volatility), 2),
    }


def analyze_market(market_data: Dict[str, pd.DataFrame]) -> Dict[str, dict]:
    results: Dict[str, dict] = {}

    for symbol, df in market_data.items():
        if df is None or len(df) < LONG_MA_WINDOW:
            continue

        asset_result = analyze_asset(df)
        if asset_result:
            results[symbol] = asset_result

    return results
