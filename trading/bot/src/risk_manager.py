class RiskManager:
    def __init__(self, config):
        self.config = config
        self.starting_balance = config.starting_balance
        self.max_daily_risk_pct = config.max_daily_risk_pct
        self.max_drawdown_pct = config.max_total_drawdown_pct
        self.risk_per_trade_pct = config.risk_per_trade_pct

        self.daily_pnl = 0.0
        self.daily_risk_used = 0.0
        self.peak_balance = self.starting_balance
        self.trading_allowed = True
        self.kill_switch_reason = None

    def update_balance(self, balance):
        """Update peak and drawdown tracking."""
        if balance > self.peak_balance:
            self.peak_balance = balance
        drawdown_pct = (self.peak_balance - balance) / self.peak_balance * 100
        if drawdown_pct >= self.max_drawdown_pct:
            self.trading_allowed = False
            self.kill_switch_reason = f"Max drawdown reached: {drawdown_pct:.2f}%"

    def can_trade(self):
        """Return True if no kill switch triggered."""
        return self.trading_allowed

    def daily_risk_remaining(self):
        max_daily = self.starting_balance * (self.max_daily_risk_pct / 100)
        return max(0, max_daily - self.daily_risk_used)

    def position_size(self, balance, stop_pips, pip_value):
        """Return lot size based on risk per trade."""
        risk_amount = balance * (self.risk_per_trade_pct / 100)
        if risk_amount > self.daily_risk_remaining():
            risk_amount = self.daily_risk_remaining()
        if risk_amount <= 0:
            return 0.0
        if stop_pips * pip_value <= 0:
            return 0.0
        lots = risk_amount / (stop_pips * pip_value)
        return round(lots, 2)

    def reset_daily(self):
        self.daily_pnl = 0.0
        self.daily_risk_used = 0.0

if __name__ == "__main__":
    import sys
    sys.path.insert(0, "..")
    from config_loader import Config
    cfg = Config("../config/config.example.yaml")
    rm = RiskManager(cfg)
    print("Can trade:", rm.can_trade())
    print("Lot size for 20-pip SL at $10/pip:", rm.position_size(50000, 20, 10))
