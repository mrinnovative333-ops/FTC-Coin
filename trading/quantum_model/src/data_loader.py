"""
Fetch multi-asset data for HETM analysis.
"""

import yfinance as yf
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

ASSETS = {
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "USDJPY": "USDJPY=X",
    "USDCAD": "USDCAD=X",
    "AUDUSD": "AUDUSD=X",
    "XAUUSD": "GC=F",      # Gold futures proxy
    "SPX": "^GSPC",        # S&P 500
    "VIX": "^VIX",
    "TNX": "^TNX",         # 10-year Treasury yield
    "BTCUSD": "BTC-USD",
    "ETHUSD": "ETH-USD",
}


def fetch_all(start="2022-01-01", end="2025-01-01"):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    assets_data = {}
    for name, ticker in ASSETS.items():
        try:
            df = yf.download(ticker, start=start, end=end, progress=False)
            if df.empty:
                print(f"[skip] {name}: no data")
                continue
            # Flatten multi-index columns if needed
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [' '.join(col).strip() for col in df.columns.values]
                rename = {}
                for c in df.columns:
                    if 'Open' in c: rename[c] = 'Open'
                    elif 'High' in c: rename[c] = 'High'
                    elif 'Low' in c: rename[c] = 'Low'
                    elif 'Close' in c: rename[c] = 'Close'
                    elif 'Adj Close' in c: rename[c] = 'Close'
                    elif 'Volume' in c: rename[c] = 'Volume'
                df = df.rename(columns=rename)
            df = df.dropna()
            df.to_csv(DATA_DIR / f"{name}.csv")
            assets_data[name] = df
            print(f"[ok] {name}: {len(df)} rows")
        except Exception as e:
            print(f"[err] {name}: {e}")
    return assets_data


if __name__ == "__main__":
    fetch_all()
