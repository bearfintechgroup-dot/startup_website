from analytics.data import get_assets
from analytics.engine import analyze_market

symbols = ["AAPL", "MSFT", "SPY"]
data = get_assets(symbols, period="3mo")

results = analyze_market(data)

print(results)
