import argparse
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from config_loader import Config
from strategy import NewsStraddleStrategy
from risk_manager import RiskManager
from broker_paper import PaperBroker
from data_feed import DataFeed
from economic_calendar import EconomicCalendar
from logger import TradeLogger


def run_backtest(config_path="../config/config.yaml", days=365, pair="EURUSD"):
    cfg = Config(config_path)
    feed = DataFeed("../data")
    cal = EconomicCalendar("../data/events.csv")
    cal.save_default()
    cal.load()

    # Fetch or load daily data
    try:
        df = feed.load_csv(pair)
    except FileNotFoundError:
        print(f"Downloading {pair} data...")
        symbol_map = {"EURUSD": "EURUSD=X", "GBPUSD": "GBPUSD=X", "USDJPY": "USDJPY=X", "XAUUSD": "GC=F"}
        df = feed.fetch_yfinance(symbol_map.get(pair, "EURUSD=X"))
        df.to_csv(f"../data/{pair}_daily.csv", index=False)

    df = df.dropna().reset_index(drop=True)

    broker = PaperBroker(starting_balance=cfg.starting_balance)
    risk = RiskManager(cfg)
    strategy = NewsStraddleStrategy(cfg, broker)
    logger = TradeLogger("../logs")

    active_signal = None
    active_order = None
    lookback = 14

    print(f"Backtesting {pair} over {len(df)} daily candles...")

    for i in range(lookback, len(df)):
        bar = df.iloc[i]
        now = bar["time"]
        current_price = bar["Close"]

        # Check if any active order should be filled or expired
        if active_order:
            filled_side = broker.check_fills(active_order, bar)
            if filled_side:
                logger.log(now, pair, f"FILL_{filled_side.upper()}", active_signal[f"{filled_side}_stop"])

        # Update open positions (SL/TP/trailing)
        if broker.positions and active_signal:
            atr_df = df.iloc[i-lookback:i]
            atr = strategy.calculate_atr(atr_df, period=cfg.strategy.get("atr_period", 14))
            if atr > 0:
                trail_amount = atr * strategy.trail_step_mult
                broker.update_positions(bar, trail_amount)

        # Cancel expired/unfilled orders
        if active_signal and strategy.should_cancel(active_signal, now, filled_side=None):
            broker.orders = []
            active_order = None
            active_signal = None
            logger.log(now, pair, "CANCEL_OCO", current_price, reason="expired")

        # Place new OCO before upcoming high-impact events
        if active_signal is None:
            upcoming = cal.upcoming_events(now, pair=pair, minutes_ahead=1440)
            if not upcoming.empty:
                event = upcoming.iloc[0]
                event_time = event["datetime"]
                minutes_until = (event_time - now).total_seconds() / 60.0

                # Place OCO on the daily candle before the event (roughly 24–48 hours out)
                if 600 <= minutes_until <= 2880:
                    atr_df = df.iloc[i-lookback:i]
                    atr = strategy.calculate_atr(atr_df, period=cfg.strategy.get("atr_period", 14))

                    if atr <= 0:
                        continue

                    active_signal = strategy.get_signal(current_price, atr, event_time, now)
                    stop_pips = abs(active_signal["buy_stop"] - active_signal["buy_sl"]) / 0.0001
                    lots = risk.position_size(broker.balance, stop_pips, 10)
                    lots = min(lots, 10.0)  # cap leverage for safety
                    active_order = broker.place_oco(
                        pair,
                        lots=lots if lots > 0 else 1.0,
                        buy_stop=active_signal["buy_stop"],
                        sell_stop=active_signal["sell_stop"],
                        buy_sl=active_signal["buy_sl"],
                        sell_sl=active_signal["sell_sl"],
                        buy_tp=active_signal["buy_tp"],
                        sell_tp=active_signal["sell_tp"],
                        timestamp=now,
                    )
                    logger.log(now, pair, "PLACE_OCO", current_price, lots=lots, signal_json=str(active_signal))
                    print(f"[{now.date()}] Place OCO before {event['event']} ({event_time.date()}) | BuyStop:{active_signal['buy_stop']:.5f} SellStop:{active_signal['sell_stop']:.5f} | Lots:{lots}")

        risk.update_balance(broker.balance)
        if not risk.can_trade():
            print(f"Kill switch: {risk.kill_switch_reason}")
            break

    summary = broker.summary()
    print("\n--- Backtest Summary ---")
    for k, v in summary.items():
        print(f"{k}: {v}")
    print(f"Log saved to: {logger.log_file}")


def run_paper(config_path="../config/config.yaml"):
    print("Paper mode requires live data feed. Use backtest mode for now.")
    print("To enable paper mode, implement live price streaming in data_feed.py")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FTC News Straddle Bot")
    parser.add_argument("--mode", choices=["backtest", "paper", "live"], default="backtest")
    parser.add_argument("--config", default="../config/config.yaml")
    parser.add_argument("--days", type=int, default=365)
    parser.add_argument("--pair", default="EURUSD")
    args = parser.parse_args()

    if args.mode == "backtest":
        run_backtest(args.config, args.days, args.pair)
    elif args.mode == "paper":
        run_paper(args.config)
    else:
        print("LIVE MODE IS DISABLED. Set mode=paper or mode=backtest.")
        sys.exit(1)
