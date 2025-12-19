import yfinance as yf


def get_assets(symbols, period="1mo"):
    """
    Fetch historical market data for a list of symbols.
    Returns a dictionary of pandas DataFrames.
    """

    data = {}

    for symbol in symbols:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period)

        if not hist.empty:
            data[symbol] = hist

    return data
