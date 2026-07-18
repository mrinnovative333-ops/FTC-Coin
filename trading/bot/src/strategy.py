import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class NewsStraddleStrategy:
    def __init__(self, config, broker, logger=None):
        self.config = config
        self.broker = broker
        self.logger = logger
        self.entry_mult = float(config.strategy.get("entry_distance_atr_multiplier", 0.5))
        self.sl_mult = float(config.strategy.get("trailing_stop_atr_multiplier", 1.0))
        self.tp_mult = float(config.strategy.get("take_profit_atr_multiplier", 2.0))
        self.trail_step_mult = float(config.strategy.get("trailing_step_atr_multiplier", 0.3))
        self.expire_after = int(config.strategy.get("expire_minutes_after_event", 30))
        self.risk_pct = config.risk_per_trade_pct

    def calculate_atr(self, df, period=14):
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return tr.rolling(window=period).mean().iloc[-1]

    def get_signal(self, current_price, atr, event_time, now):
        """
        Returns OCO bracket: dict with buy_stop, sell_stop, stop_loss, take_profit sizes.
        """
        distance = atr * self.entry_mult
        buy_stop = current_price + distance
        sell_stop = current_price - distance

        # Stop loss is trailing distance on the opposite side of entry
        buy_sl = buy_stop - (atr * self.sl_mult)
        sell_sl = sell_stop + (atr * self.sl_mult)

        # Take profit targets
        buy_tp = buy_stop + (atr * self.tp_mult)
        sell_tp = sell_stop - (atr * self.tp_mult)

        minutes_until = (event_time - now).total_seconds() / 60.0

        signal = {
            "type": "oco_straddle",
            "timestamp": now,
            "event_time": event_time,
            "current_price": current_price,
            "atr": atr,
            "buy_stop": buy_stop,
            "sell_stop": sell_stop,
            "buy_sl": buy_sl,
            "buy_tp": buy_tp,
            "sell_sl": sell_sl,
            "sell_tp": sell_tp,
            "risk_pct": self.risk_pct,
            "minutes_until_event": minutes_until,
        }
        return signal

    def should_cancel(self, signal, now, filled_side=None):
        """Cancel unfilled orders after event + expiration window or if one side filled."""
        if filled_side is not None:
            return True
        event_time = signal["event_time"]
        if now > event_time + timedelta(minutes=self.expire_after):
            return True
        return False

    def trail_stop(self, entry, current, side, trail_amount, last_trail_stop):
        """Simple trailing stop update."""
        if side == "buy":
            new_stop = current - trail_amount
            if last_trail_stop is None:
                return new_stop
            return max(new_stop, last_trail_stop)
        else:
            new_stop = current + trail_amount
            if last_trail_stop is None:
                return new_stop
            return min(new_stop, last_trail_stop)

if __name__ == "__main__":
    # Quick sanity test
    import sys
    sys.path.insert(0, "..")
    from config_loader import Config
    cfg = Config("../config/config.example.yaml")

    class FakeBroker:
        pass

    strat = NewsStraddleStrategy(cfg, FakeBroker())
    df = pd.DataFrame({
        'High': [1.0800, 1.0810, 1.0820],
        'Low': [1.0780, 1.0790, 1.0800],
        'Close': [1.0790, 1.0800, 1.0810]
    })
    atr = strat.calculate_atr(df, period=2)
    signal = strat.get_signal(1.0810, atr, datetime.now() + timedelta(minutes=5), datetime.now())
    print(signal)
