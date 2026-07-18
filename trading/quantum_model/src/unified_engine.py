"""
Unified trading engine for FTC research.
Combines:
  1. News Straddle Strategy
  2. Holographic Entanglement Trading Model (HETM)
  3. Hybrid: HETM direction filter + News Straddle execution

All strategies use proper risk-based lot sizing with a hard lot cap,
and account for spread/commission transaction costs.
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Optional, Dict, List
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from hetm_core import EntanglementBulk


@dataclass
class TradeConfig:
    starting_balance: float = 50000.0
    risk_per_trade_pct: float = 1.0      # default 1% per trade
    max_lots_hard_cap: float = 5.0       # your constraint
    spread_pips: float = 1.0              # typical spread cost
    commission_per_lot: float = 0.0       # optional
    kill_switch_drawdown_pct: float = 10.0
    max_daily_risk_pct: float = 2.0


class RiskManager:
    def __init__(self, cfg: TradeConfig):
        self.cfg = cfg
        self.balance = cfg.starting_balance
        self.peak = cfg.starting_balance
        self.daily_pnl = 0.0
        self.last_date = None

    def update(self, date, new_balance):
        if self.last_date is not None and date != self.last_date:
            self.daily_pnl = 0.0
        self.last_date = date
        self.balance = new_balance
        if new_balance > self.peak:
            self.peak = new_balance

    def position_size(self, stop_pips: float, pip_value: float = 10.0) -> float:
        """
        Risk-based lot sizing with hard lot cap.
        """
        if stop_pips <= 0:
            return 0.0
        risk_dollars = self.cfg.risk_per_trade_pct / 100.0 * self.balance
        lots = risk_dollars / (stop_pips * pip_value)
        return min(lots, self.cfg.max_lots_hard_cap)

    def cost_per_trade(self, lots: float) -> float:
        spread_cost = lots * self.cfg.spread_pips * 10.0
        commission_cost = lots * self.cfg.commission_per_lot
        return spread_cost + commission_cost

    def kill_switch(self) -> bool:
        dd = (self.peak - self.balance) / self.peak * 100.0
        if dd >= self.cfg.kill_switch_drawdown_pct:
            return True
        if abs(self.daily_pnl) / self.cfg.starting_balance * 100 >= self.cfg.max_daily_risk_pct:
            return True
        return False


class UnifiedBroker:
    """
    Paper broker supporting OCO bracket orders, trailing stops, and costs.
    """
    def __init__(self, cfg: TradeConfig):
        self.cfg = cfg
        self.risk = RiskManager(cfg)
        self.balance = cfg.starting_balance
        self.orders: List[Dict] = []
        self.positions: List[Dict] = []
        self.trade_log: List[Dict] = []
        self.order_id = 0

    def place_oco(self, pair, lots, buy_stop, sell_stop, buy_sl, sell_sl, buy_tp, sell_tp,
                    trail_amount, timestamp):
        self.order_id += 1
        order = {
            "id": self.order_id,
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
            "trail_amount": trail_amount,
            "placed_at": timestamp,
        }
        self.orders.append(order)
        return order

    def check_fills(self, order, bar):
        if order["active_buy"] and bar["High"] >= order["buy_stop"]:
            self._open_position(order, "buy", order["buy_stop"], order["buy_sl"], order["buy_tp"], bar["time"])
            order["active_buy"] = False
            order["active_sell"] = False
            return "buy"
        if order["active_sell"] and bar["Low"] <= order["sell_stop"]:
            self._open_position(order, "sell", order["sell_stop"], order["sell_sl"], order["sell_tp"], bar["time"])
            order["active_buy"] = False
            order["active_sell"] = False
            return "sell"
        return None

    def _open_position(self, order, side, entry, sl, tp, time):
        cost = self.risk.cost_per_trade(order["lots"])
        self.balance -= cost
        self.positions.append({
            "pair": order["pair"],
            "side": side,
            "lots": order["lots"],
            "entry": entry,
            "sl": sl,
            "tp": tp,
            "open_time": time,
            "trail": sl,
            "trail_amount": order.get("trail_amount", 0.0001),
        })
        self.trade_log.append({
            "time": time,
            "pair": order["pair"],
            "action": f"OPEN_{side.upper()}",
            "price": entry,
            "lots": order["lots"],
            "cost": cost,
            "balance": self.balance,
        })

    def update_positions(self, bar):
        closed = []
        for pos in list(self.positions):
            if pos["side"] == "buy":
                # SL hit
                if bar["Low"] <= pos["sl"]:
                    self._close_position(pos, bar["time"], pos["sl"], "SL")
                    closed.append(pos)
                    continue
                # TP hit
                if bar["High"] >= pos["tp"]:
                    self._close_position(pos, bar["time"], pos["tp"], "TP")
                    closed.append(pos)
                    continue
                # Trailing stop
                new_trail = bar["Close"] - pos["trail_amount"]
                if new_trail > pos["trail"]:
                    pos["trail"] = new_trail
                    pos["sl"] = max(pos["sl"], new_trail)
            else:
                if bar["High"] >= pos["sl"]:
                    self._close_position(pos, bar["time"], pos["sl"], "SL")
                    closed.append(pos)
                    continue
                if bar["Low"] <= pos["tp"]:
                    self._close_position(pos, bar["time"], pos["tp"], "TP")
                    closed.append(pos)
                    continue
                new_trail = bar["Close"] + pos["trail_amount"]
                if new_trail < pos["trail"]:
                    pos["trail"] = new_trail
                    pos["sl"] = min(pos["sl"], new_trail)
        return closed

    def _close_position(self, pos, time, price, reason):
        if pos["side"] == "buy":
            pips = (price - pos["entry"]) / 0.0001
        else:
            pips = (pos["entry"] - price) / 0.0001
        gross_pnl = pips * pos["lots"] * 10.0
        cost = self.risk.cost_per_trade(pos["lots"])
        net_pnl = gross_pnl - cost
        self.balance += net_pnl
        self.positions.remove(pos)
        self.trade_log.append({
            "time": time,
            "pair": pos["pair"],
            "action": f"CLOSE_{reason}",
            "price": price,
            "lots": pos["lots"],
            "gross_pnl": gross_pnl,
            "cost": cost,
            "net_pnl": net_pnl,
            "balance": self.balance,
        })

    def summary(self):
        closes = [t for t in self.trade_log if "CLOSE" in t["action"]]
        wins = [t for t in closes if t["net_pnl"] > 0]
        losses = [t for t in closes if t["net_pnl"] <= 0]
        total = sum(t["net_pnl"] for t in closes)
        gross = sum(t["gross_pnl"] for t in closes)
        costs = sum(t["cost"] for t in closes)
        return {
            "balance": self.balance,
            "total_trades": len(closes),
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": len(wins) / len(closes) * 100 if closes else 0,
            "total_net_pnl": total,
            "total_gross_pnl": gross,
            "total_costs": costs,
            "avg_net_pnl": total / len(closes) if closes else 0,
            "return_pct": (self.balance / self.cfg.starting_balance - 1) * 100,
        }


def calc_atr(df, period=14):
    tr1 = df["High"] - df["Low"]
    tr2 = abs(df["High"] - df["Close"].shift(1))
    tr3 = abs(df["Low"] - df["Close"].shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(period, min_periods=1).mean().iloc[-1]


class StraddleStrategy:
    """
    Classic news straddle: place OCO buy/sell stops before high-impact events.
    """
    def __init__(self, cfg: TradeConfig):
        self.cfg = cfg

    def signal(self, df, event_time, timestamp, lookback=14, atr_mult=1.0, sl_mult=2.0, tp_mult=4.0, trail_mult=1.0):
        atr = calc_atr(df.iloc[-lookback:], period=lookback)
        if atr <= 0:
            return None
        price = df["Close"].iloc[-1]
        buy_stop = price + atr * atr_mult
        sell_stop = price - atr * atr_mult
        return {
            "buy_stop": buy_stop,
            "sell_stop": sell_stop,
            "buy_sl": price - atr * sl_mult,
            "sell_sl": price + atr * sl_mult,
            "buy_tp": price + atr * tp_mult,
            "sell_tp": price - atr * tp_mult,
            "trail_amount": atr * trail_mult,
            "stop_pips": abs(buy_stop - (price - atr * sl_mult)) / 0.0001,
        }


class HETMStrategy:
    """
    Quantum-inspired holographic directional strategy.
    """
    def __init__(self, cfg: TradeConfig):
        self.cfg = cfg

    def signal(self, assets_data, target="EURUSD", train_window=60, er_threshold=0.2, lookback=20):
        bulk = EntanglementBulk(assets_data, lookback=train_window, er_threshold=er_threshold)
        if target not in bulk.qubits:
            return {"direction": 0, "confidence": 0.0, "rationale": "target not in bulk"}

        from hetm_core import HolographicTrader
        trader = HolographicTrader(bulk, target_asset=target)
        return trader.signal(lookback=lookback)


class HybridStrategy:
    """
    Hybrid: use HETM direction as a filter on which side of the straddle to favor,
    or skip if confidence is too low.
    """
    def __init__(self, cfg: TradeConfig, hetm_bias_threshold=0.5):
        self.cfg = cfg
        self.straddle = StraddleStrategy(cfg)
        self.hetm = HETMStrategy(cfg)
        self.bias_threshold = hetm_bias_threshold

    def signal(self, df, assets_data, event_time, timestamp, **kwargs):
        straddle = self.straddle.signal(df, event_time, timestamp, **kwargs)
        if straddle is None:
            return None

        hetm_sig = self.hetm.signal(assets_data, target="EURUSD", train_window=60)
        if hetm_sig["confidence"] > self.bias_threshold:
            # Filter to only one direction if HETM is confident
            if hetm_sig["direction"] == 1:
                straddle["sell_stop"] = None  # remove sell side
            elif hetm_sig["direction"] == -1:
                straddle["buy_stop"] = None
            straddle["hetm_bias"] = hetm_sig["direction"]
            straddle["hetm_confidence"] = hetm_sig["confidence"]
        else:
            straddle["hetm_bias"] = 0
            straddle["hetm_confidence"] = hetm_sig["confidence"]
        return straddle


def run_straddle_backtest(df_daily, events, cfg: TradeConfig, pair="EURUSD"):
    broker = UnifiedBroker(cfg)
    strategy = StraddleStrategy(cfg)
    active_order = None
    active_signal = None

    for i in range(60, len(df_daily)):
        bar = df_daily.iloc[i]
        now = bar["time"]
        price = bar["Close"]

        if active_order:
            broker.check_fills(active_order, bar)
            broker.update_positions(bar)

        # Cancel if expired (OCO valid until next event or 3 days)
        if active_signal and active_signal["event_time"] <= now:
            broker.orders = []
            active_order = None
            active_signal = None

        if active_signal is None:
            # Find next event between 1 and 3 days out
            future = events[events["datetime"] > now]
            if len(future) == 0:
                continue
            next_event = future.iloc[0]
            minutes_until = (next_event["datetime"] - now).total_seconds() / 60.0
            if 360 <= minutes_until <= 2160:  # 6 hours to 36 hours
                sig = strategy.signal(df_daily.iloc[i-30:i], next_event["datetime"], now,
                                      lookback=14, atr_mult=0.5, sl_mult=1.5, tp_mult=3.0, trail_mult=0.7)
                if sig is None:
                    continue
                lots = broker.risk.position_size(sig["stop_pips"])
                active_order = broker.place_oco(
                    pair, lots,
                    sig["buy_stop"], sig["sell_stop"],
                    sig["buy_sl"], sig["sell_sl"],
                    sig["buy_tp"], sig["sell_tp"],
                    sig["trail_amount"], now
                )
                active_signal = dict(sig)
                active_signal["event_time"] = next_event["datetime"]

        broker.risk.update(now, broker.balance)
        if broker.risk.kill_switch():
            print(f"Kill switch at {now.date()}: balance=${broker.balance:.2f}")
            break

    return broker


def run_hetm_backtest(closes, assets_data, cfg: TradeConfig, target="EURUSD", train_window=60):
    broker = UnifiedBroker(cfg)
    # Simplified HETM directional day-trading
    for i in range(train_window, len(closes)):
        date = closes.index[i]
        price = closes[target].iloc[i]
        prev_price = closes[target].iloc[i - 1]

        # Build window assets for bulk geometry
        window_assets = {}
        for name, df in assets_data.items():
            try:
                end_loc = df.index.get_loc(date)
                if end_loc < train_window:
                    continue
                window_assets[name] = df.iloc[end_loc - train_window:end_loc]
            except KeyError:
                continue

        sig = {"direction": 0, "confidence": 0.0}
        if len(window_assets) >= 3:
            hetm = HETMStrategy(cfg)
            sig = hetm.signal(window_assets, target=target, train_window=train_window)

        desired = sig["direction"] if sig["confidence"] > 0.35 else 0

        # Close if direction flips
        if broker.positions:
            pos = broker.positions[0]
            current_side = 1 if pos["side"] == "buy" else -1
            if desired != current_side:
                broker._close_position(pos, date, price, "FLIP")

        # Open new directional trade
        if not broker.positions and desired != 0:
            side = "buy" if desired == 1 else "sell"
            stop_pips = 20.0
            lots = broker.risk.position_size(stop_pips)
            sl = price - stop_pips * 0.0001 if side == "buy" else price + stop_pips * 0.0001
            tp = price + stop_pips * 0.0004 if side == "buy" else price - stop_pips * 0.0004
            trail = stop_pips * 0.0001
            order = {
                "pair": target, "lots": lots,
                "buy_stop": price, "sell_stop": price,
                "buy_sl": sl, "sell_sl": sl,
                "buy_tp": tp, "sell_tp": tp,
                "trail_amount": trail
            }
            broker._open_position(order, side, price, sl, tp, date)

        bar = {"time": date, "Open": prev_price, "High": max(price, prev_price),
               "Low": min(price, prev_price), "Close": price}
        broker.update_positions(bar)
        broker.risk.update(date, broker.balance)
        if broker.risk.kill_switch():
            print(f"Kill switch at {date.date()}: balance=${broker.balance:.2f}")
            break

    return broker


def run_hybrid_backtest(closes, assets_data, events, cfg: TradeConfig, pair="EURUSD", train_window=60):
    """
    Hybrid: News straddle with HETM directional bias filter.
    """
    broker = UnifiedBroker(cfg)
    strategy = StraddleStrategy(cfg)
    active_order = None
    active_signal = None

    for i in range(max(train_window, 30), len(closes)):
        date = closes.index[i]
        price = closes[pair].iloc[i]
        prev_price = closes[pair].iloc[i - 1]

        bar = {"time": date, "Open": prev_price, "High": max(price, prev_price),
               "Low": min(price, prev_price), "Close": price}

        if active_order:
            broker.check_fills(active_order, bar)
            broker.update_positions(bar)

        if active_signal and active_signal["event_time"] <= date:
            broker.orders = []
            active_order = None
            active_signal = None

        if active_signal is None:
            future = events[events["datetime"] > date]
            if len(future) == 0:
                continue
            next_event = future.iloc[0]
            minutes_until = (next_event["datetime"] - date).total_seconds() / 60.0
            if 360 <= minutes_until <= 2160:
                # Build window assets for HETM bias
                window_assets = {}
                for name, df in assets_data.items():
                    try:
                        end_loc = df.index.get_loc(date)
                        if end_loc < train_window:
                            continue
                        window_assets[name] = df.iloc[end_loc - train_window:end_loc]
                    except KeyError:
                        continue

                straddle = strategy.signal(
                    pd.DataFrame({"time": closes.index[:i+1], "Close": closes[pair].iloc[:i+1],
                                  "High": closes[pair].iloc[:i+1], "Low": closes[pair].iloc[:i+1]}),
                    next_event["datetime"], date,
                    lookback=14, atr_mult=0.5, sl_mult=1.5, tp_mult=3.0, trail_mult=0.7
                )
                if straddle is None:
                    continue

                # Apply HETM bias if confident
                if len(window_assets) >= 3:
                    hetm = HETMStrategy(cfg)
                    hetm_sig = hetm.signal(window_assets, target=pair, train_window=train_window)
                    if hetm_sig["confidence"] > 0.35 and hetm_sig["direction"] != 0:
                        if hetm_sig["direction"] == 1:
                            straddle["sell_stop"] = None
                        else:
                            straddle["buy_stop"] = None

                lots = broker.risk.position_size(straddle["stop_pips"])
                active_order = broker.place_oco(
                    pair, lots,
                    straddle["buy_stop"], straddle["sell_stop"],
                    straddle["buy_sl"], straddle["sell_sl"],
                    straddle["buy_tp"], straddle["sell_tp"],
                    straddle["trail_amount"], date
                )
                active_signal = dict(straddle)
                active_signal["event_time"] = next_event["datetime"]

        broker.risk.update(date, broker.balance)
        if broker.risk.kill_switch():
            print(f"Hybrid kill switch at {date.date()}: balance=${broker.balance:.2f}")
            break

    return broker


if __name__ == "__main__":
    print("Unified trading engine loaded. Use run_straddle_backtest() or run_hetm_backtest().")
