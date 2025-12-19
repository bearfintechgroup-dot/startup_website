import pandas as pd

def _to_series(x):
    # yfinance sometimes returns a DataFrame column (e.g., multi-index / adjusted behavior)
    if isinstance(x, pd.DataFrame):
        return x.iloc[:, 0]
    return x

def analyze_asset(df: pd.DataFrame):
    close = _to_series(df["Close"]).dropna()

    returns = close.pct_change()
    total_return = (close.iloc[-1] / close.iloc[0] - 1) * 100

    short_ma = close.rolling(window=10).mean()
    long_ma  = close.rolling(window=30).mean()

    short_last = float(short_ma.iloc[-1])
    long_last  = float(long_ma.iloc[-1])

    trend = "Bullish" if short_last > long_last else "Bearish"

    # Strength: % distance between MAs (simple + readable)
    trend_strength = ((short_last - long_last) / long_last) * 100 if long_last != 0 else 0.0

    # Momentum: last 10 bars delta (guard length)
    momentum = float(close.iloc[-1] - close.iloc[-10]) if len(close) >= 10 else 0.0

    volatility = float(returns.std() * (252 ** 0.5))

    # Simple label for UI
    if trend == "Bullish" and trend_strength > 0.4:
        signal = "Strong Bullish"
    elif trend == "Bearish" and trend_strength < -0.4:
        signal = "Strong Bearish"
    else:
        signal = "Neutral"

    return {
        "price": float(round(close.iloc[-1], 2)),
        "total_return": float(round(total_return, 2)),
        "trend": trend,
        "trend_strength": float(round(trend_strength, 2)),
        "signal": signal,
        "momentum": float(round(momentum, 2)),
        "volatility": float(round(volatility, 2)),
    }

def analyze_market(market_data: dict):
    results = {}
    for symbol, df in market_data.items():
        if df is not None and len(df) >= 30:
            results[symbol] = analyze_asset(df)
    return results
