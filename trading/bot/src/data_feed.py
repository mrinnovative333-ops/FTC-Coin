import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

class DataFeed:
    """
    Loads price data from CSV or yfinance.
    """
    def __init__(self, data_dir="../data"):
        self.data_dir = Path(data_dir)

    def load_csv(self, symbol):
        path = self.data_dir / f"{symbol}_daily.csv"
        if not path.exists():
            raise FileNotFoundError(f"No data file: {path}")
        df = pd.read_csv(path)
        # Support either 'time' or 'Date' column
        date_col = "time" if "time" in df.columns else "Date"
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.rename(columns={date_col: "time"})
        df = df.sort_values("time").reset_index(drop=True)
        return df

    def fetch_yfinance(self, symbol, start="2022-01-01", end="2025-01-01"):
        import yfinance as yf
        df = yf.download(symbol, start=start, end=end, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [' '.join(col).strip() for col in df.columns.values]
            rename_map = {}
            for c in df.columns:
                if 'Open' in c: rename_map[c] = 'Open'
                elif 'High' in c: rename_map[c] = 'High'
                elif 'Low' in c: rename_map[c] = 'Low'
                elif 'Close' in c: rename_map[c] = 'Close'
            df = df.rename(columns=rename_map)
        df = df.reset_index()
        df = df.rename(columns={"Date": "time"})
        return df

    def resample_to_4h(self, df):
        """Convert daily data to 4H for backtest granularity."""
        df = df.set_index("time")
        ohlc = df.resample("4h").agg({
            "Open": "first",
            "High": "max",
            "Low": "min",
            "Close": "last",
        }).dropna()
        ohlc = ohlc.reset_index()
        return ohlc

if __name__ == "__main__":
    feed = DataFeed("../data")
    df = feed.fetch_yfinance("EURUSD=X", start="2023-01-01", end="2024-12-31")
    print(df.tail())
    df.to_csv("../data/EURUSD_daily.csv", index=False)
