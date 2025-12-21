import pandas as pd
from typing import Dict

# ============================================================
# Configuration / Constants
# ============================================================
SHORT_TERM_FAST_MA = 5
SHORT_TERM_SLOW_MA = 10
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
def analyze_asset(df: pd.DataFrame, period: str) -> Dict[str, float | str]:
    close = _to_series(df["Close"]).dropna()
    if close.empty:
        return {}

    returns = close.pct_change()
    total_return = (close.iloc[-1] / close.iloc[0] - 1) * 100
    momentum = float(close.iloc[-1] - close.iloc[0])
    volatility = float(returns.std() * (TRADING_DAYS_PER_YEAR ** 0.5))

    # -----------------------------
    # SHORT-TERM MODES
    # -----------------------------
    if period == "5d":
        # Ultra-short horizon: no moving averages
        if len(close) < 2:
            return {}

        signal = "Short-Term Momentum"

        return {
            "price": round(float(close.iloc[-1]), 2),
            "total_return": round(float(total_return), 2),
            "trend": "Momentum",
            "trend_strength": 0.0,
            "signal": signal,
            "momentum": round(float(momentum), 2),
            "volatility": round(float(volatility), 2),
        }

    if period == "1mo":
        if len(close) < SHORT_TERM_SLOW_MA:
            return {}

        ma_fast = close.rolling(SHORT_TERM_FAST_MA).mean()
        ma_slow = close.rolling(SHORT_TERM_SLOW_MA).mean()

        fast_last = float(ma_fast.iloc[-1])
        slow_last = float(ma_slow.iloc[-1])

        trend = "Bullish" if fast_last > slow_last else "Bearish"
        trend_strength = (
            ((fast_last - slow_last) / slow_last) * 100
            if slow_last != 0
            else 0.0
        )

        signal = "Short-Term Bullish" if trend == "Bullish" else "Short-Term Bearish"

        return {
            "price": round(float(close.iloc[-1]), 2),
            "total_return": round(float(total_return), 2),
            "trend": trend,
            "trend_strength": round(float(trend_strength), 2),
            "signal": signal,
            "momentum": round(float(momentum), 2),
            "volatility": round(float(volatility), 2),
        }

    # -----------------------------
    # TREND MODE (3M+)
    # -----------------------------
    if len(close) < LONG_MA_WINDOW:
        return {}

    short_ma = close.rolling(SHORT_MA_WINDOW).mean()
    long_ma = close.rolling(LONG_MA_WINDOW).mean()

    short_last = float(short_ma.iloc[-1])
    long_last = float(long_ma.iloc[-1])

    trend = "Bullish" if short_last > long_last else "Bearish"
    trend_strength = (
        ((short_last - long_last) / long_last) * 100
        if long_last != 0
        else 0.0
    )

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


def analyze_market(market_data: Dict[str, pd.DataFrame], period: str) -> Dict[str, dict]:
    results: Dict[str, dict] = {}

    for symbol, df in market_data.items():
        if df is None or df.empty:
            continue

        asset_result = analyze_asset(df, period)
        if asset_result:
            results[symbol] = asset_result

    return results

def compute_market_regime(results: Dict[str, dict]) -> dict:
    if not results:
        return {
            "label": "No Data",
            "score": 0,
        }

    bullish = 0
    bearish = 0

    for r in results.values():
        signal = r.get("signal", "")
        if "Bullish" in signal:
            bullish += 1
        elif "Bearish" in signal:
            bearish += 1

    total = bullish + bearish
    if total == 0:
        return {"label": "Neutral", "score": 50}

    ratio = bullish / total

    if ratio >= 0.65:
        return {"label": "Risk-On", "score": int(ratio * 100)}
    elif ratio <= 0.35:
        return {"label": "Risk-Off", "score": int(ratio * 100)}
    else:
        return {"label": "Transitional", "score": int(ratio * 100)}
