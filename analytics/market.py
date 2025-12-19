import yfinance as yf

DEFAULT_SYMBOLS = ["AAPL", "MSFT", "SPY"]

def fetch_market_data(symbols=None, period="3mo"):
    symbols = symbols or DEFAULT_SYMBOLS

    data = {}
    for symbol in symbols:
        df = yf.download(symbol, period=period, progress=False, auto_adjust=False)
        data[symbol] = df
    return data
