import pandas as pd
from datetime import datetime

class PaperBroker:
    """
    Simulated broker for backtesting and paper trading.
    Tracks positions, orders, balance, and PnL.
    """
    def __init__(self, starting_balance=50000, pip_value_per_lot=10):
        self.balance = starting_balance
        self.pip_value_per_lot = pip_value_per_lot
        self.positions = []
        self.orders = []
        self.trade_log = []
        self.order_id_counter = 0

    def place_oco(self, pair, lots, buy_stop, sell_stop, buy_sl, sell_sl, buy_tp, sell_tp, timestamp):
        self.order_id_counter += 1
        order = {
            "id": self.order_id_counter,
            "pair": pair,
            "lots": lots,
            "buy_stop": buy_stop,
            "sell_stop": sell_stop,
            "buy_sl": buy_sl,
            "sell_sl": sell_sl,
            "buy_tp": buy_tp,
            "sell_tp": sell_tp,
            "active_buy": True,
            "active_sell": True,
            "placed_at": timestamp,
        }
        self.orders.append(order)
        return order

    def cancel_opposite(self, order, filled_side):
        if filled_side == "buy":
            order["active_sell"] = False
        else:
            order["active_buy"] = False

    def check_fills(self, order, bar):
        """Check if buy_stop or sell_stop orders would fill on this bar."""
        filled_side = None
        if order["active_buy"] and bar["High"] >= order["buy_stop"]:
            filled_side = "buy"
            entry = order["buy_stop"]
            sl = order["buy_sl"]
            tp = order["buy_tp"]
            order["active_buy"] = False
            order["active_sell"] = False  # cancel opposite
            self.positions.append({
                "pair": order["pair"],
                "side": "buy",
                "lots": order["lots"],
                "entry": entry,
                "sl": sl,
                "tp": tp,
                "open_time": bar["time"],
                "trailing_stop": sl,
            })
            self.trade_log.append({
                "time": bar["time"],
                "pair": order["pair"],
                "action": "OPEN_BUY",
                "price": entry,
                "lots": order["lots"],
            })
        elif order["active_sell"] and bar["Low"] <= order["sell_stop"]:
            filled_side = "sell"
            entry = order["sell_stop"]
            sl = order["sell_sl"]
            tp = order["sell_tp"]
            order["active_buy"] = False
            order["active_sell"] = False
            self.positions.append({
                "pair": order["pair"],
                "side": "sell",
                "lots": order["lots"],
                "entry": entry,
                "sl": sl,
                "tp": tp,
                "open_time": bar["time"],
                "trailing_stop": sl,
            })
            self.trade_log.append({
                "time": bar["time"],
                "pair": order["pair"],
                "action": "OPEN_SELL",
                "price": entry,
                "lots": order["lots"],
            })
        return filled_side

    def update_positions(self, bar, trail_amount):
        closed_positions = []
        for pos in self.positions[:]:
            pips = self.pip_value_per_lot
            # Check SL and TP
            if pos["side"] == "buy":
                if bar["Low"] <= pos["sl"]:
                    pnl = -(pos["entry"] - pos["sl"]) * pos["lots"] * 100000  # rough USD pnl for forex
                    self.close_position(pos, bar["time"], pos["sl"], "SL", pnl)
                    closed_positions.append(pos)
                    continue
                if bar["High"] >= pos["tp"]:
                    pnl = (pos["tp"] - pos["entry"]) * pos["lots"] * 100000
                    self.close_position(pos, bar["time"], pos["tp"], "TP", pnl)
                    closed_positions.append(pos)
                    continue
                # Update trailing stop
                new_trail = bar["Close"] - trail_amount
                if new_trail > pos["trailing_stop"]:
                    pos["trailing_stop"] = new_trail
                    pos["sl"] = new_trail
            else:
                if bar["High"] >= pos["sl"]:
                    pnl = -(pos["sl"] - pos["entry"]) * pos["lots"] * 100000
                    self.close_position(pos, bar["time"], pos["sl"], "SL", pnl)
                    closed_positions.append(pos)
                    continue
                if bar["Low"] <= pos["tp"]:
                    pnl = (pos["entry"] - pos["tp"]) * pos["lots"] * 100000
                    self.close_position(pos, bar["time"], pos["tp"], "TP", pnl)
                    closed_positions.append(pos)
                    continue
                new_trail = bar["Close"] + trail_amount
                if new_trail < pos["trailing_stop"]:
                    pos["trailing_stop"] = new_trail
                    pos["sl"] = new_trail
        return closed_positions

    def close_position(self, pos, time, price, reason, pnl):
        self.positions.remove(pos)
        # For forex: 1 standard lot = $10 per pip on most pairs
        # PnL in USD = (price_diff / 0.0001) * lots * 10
        if pos["side"] == "buy":
            pips = (price - pos["entry"]) / 0.0001
        else:
            pips = (pos["entry"] - price) / 0.0001
        pnl = pips * pos["lots"] * 10
        self.balance += pnl
        self.trade_log.append({
            "time": time,
            "pair": pos["pair"],
            "action": f"CLOSE_{reason}",
            "price": price,
            "lots": pos["lots"],
            "pnl": pnl,
        })

    def summary(self):
        trades = [t for t in self.trade_log if "CLOSE" in t["action"]]
        wins = [t for t in trades if t.get("pnl", 0) > 0]
        losses = [t for t in trades if t.get("pnl", 0) <= 0]
        total_pnl = sum(t.get("pnl", 0) for t in trades)
        return {
            "balance": self.balance,
            "total_trades": len(trades),
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": len(wins) / len(trades) * 100 if trades else 0,
            "total_pnl": total_pnl,
            "avg_pnl": total_pnl / len(trades) if trades else 0,
        }

if __name__ == "__main__":
    b = PaperBroker()
    print("Paper broker initialized with $", b.balance)
