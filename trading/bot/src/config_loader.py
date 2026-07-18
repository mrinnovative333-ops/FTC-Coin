import yaml
import os
from pathlib import Path

class Config:
    def __init__(self, path="config/config.yaml"):
        self.path = Path(path)
        if not self.path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        with open(self.path, "r") as f:
            self.raw = yaml.safe_load(f)

        self.mode = self.raw.get("mode", "paper")
        self.account = self.raw.get("account", {})
        self.risk = self.raw.get("risk", {})
        self.strategy = self.raw.get("strategy", {})
        self.calendar = self.raw.get("calendar", {})
        self.broker = self.raw.get("broker", {})
        self.logging = self.raw.get("logging", {})
        self.notifications = self.raw.get("notifications", {})

    @property
    def starting_balance(self):
        return float(self.account.get("starting_balance", 10000))

    @property
    def max_daily_risk_pct(self):
        return float(self.account.get("max_daily_risk_pct", 2.0))

    @property
    def max_total_drawdown_pct(self):
        return float(self.account.get("max_total_drawdown_pct", 6.0))

    @property
    def risk_per_trade_pct(self):
        return float(self.risk.get("risk_per_trade_pct", 1.0))

    @property
    def pairs(self):
        return self.strategy.get("pairs", ["EURUSD"])

    @property
    def news_events(self):
        return self.strategy.get("news_filter", [])

if __name__ == "__main__":
    # Test
    cfg = Config("config/config.example.yaml")
    print(cfg.mode, cfg.pairs, cfg.news_events)
