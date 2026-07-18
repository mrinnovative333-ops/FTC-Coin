import pandas as pd
from datetime import datetime, timedelta
import json

class EconomicCalendar:
    """
    Loads and queries economic events.
    Supports manual CSV input and placeholder for external feeds.
    """
    def __init__(self, path="../data/events.csv"):
        self.path = path
        self.events = None

    def load(self):
        try:
            df = pd.read_csv(self.path, parse_dates=["datetime"])
        except FileNotFoundError:
            df = self._default_events()
        df = df.sort_values("datetime").reset_index(drop=True)
        self.events = df
        return df

    def _default_events(self):
        # Generate NFP-like events across 2023-2024 to overlap with downloaded data
        events = []
        start = pd.Timestamp("2023-02-03 08:30")
        for i in range(24):
            t = start + pd.DateOffset(months=i)
            if t.year > 2024:
                break
            events.append({"datetime": t, "pair": "EURUSD", "event": "Non-Farm Payrolls", "impact": "High"})
            events.append({"datetime": t + pd.DateOffset(days=7, hours=2), "pair": "EURUSD", "event": "CPI", "impact": "High"})
        df = pd.DataFrame(events)
        df["datetime"] = pd.to_datetime(df["datetime"])
        return df

    def upcoming_events(self, now, pair=None, minutes_ahead=60):
        if self.events is None:
            self.load()
        mask = (self.events["datetime"] > now) & (self.events["datetime"] <= now + timedelta(minutes=minutes_ahead))
        if pair:
            mask = mask & (self.events["pair"] == pair)
        return self.events[mask]

    def save_default(self):
        df = self._default_events()
        df.to_csv(self.path, index=False)

if __name__ == "__main__":
    cal = EconomicCalendar("../data/events.csv")
    cal.save_default()
    df = cal.load()
    print(df)
