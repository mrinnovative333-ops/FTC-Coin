"""
Backtest the Holographic Entanglement Trading Model (HETM).
Walk forward: each day, rebuild bulk geometry, generate signal, execute paper trade.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
import numpy as np
from hetm_core import EntanglementBulk, HolographicTrader
from data_loader import DATA_DIR, ASSETS


def load_assets_data(start=None, end=None):
    assets_data = {}
    for name in ASSETS.keys():
        path = DATA_DIR / f"{name}.csv"
        if not path.exists():
            continue
        df = pd.read_csv(path, parse_dates=["time" if "time" in pd.read_csv(path, nrows=0).columns else "Date"])
        date_col = "time" if "time" in df.columns else "Date"
        df = df.rename(columns={date_col: "time"})
        df = df.set_index("time")
        df = df.dropna()
        if start:
            df = df[df.index >= start]
        if end:
            df = df[df.index <= end]
        if len(df) > 30:
            assets_data[name] = df
    return assets_data


def run_backtest(target="EURUSD", train_window=60, start_date="2023-06-01", end_date="2024-12-31"):
    assets_data = load_assets_data()
    if target not in assets_data:
        print(f"Target {target} not available. Run data_loader.py first.")
        return

    # Build a common date index
    closes = pd.DataFrame({name: df["Close"] for name, df in assets_data.items()})
    closes = closes.dropna()
    closes = closes[(closes.index >= start_date) & (closes.index <= end_date)]

    balance = 100000.0
    trades = []
    position = 0  # +1 long, -1 short, 0 flat
    entry_price = None

    print(f"Running HETM backtest on {target}: {len(closes)} days")

    for i in range(train_window, len(closes)):
        current_date = closes.index[i]
        current_price = closes[target].iloc[i]

        # Build bulk geometry from previous train_window days
        window_assets = {}
        for name, df in assets_data.items():
            try:
                end_loc = df.index.get_loc(current_date)
                if end_loc < train_window:
                    continue
                window = df.iloc[end_loc - train_window:end_loc]
                if len(window) >= train_window // 2:
                    window_assets[name] = window
            except KeyError:
                continue

        if len(window_assets) < 3:
            continue

        bulk = EntanglementBulk(window_assets, lookback=train_window, er_threshold=0.2)
        if target not in bulk.qubits:
            continue

        trader = HolographicTrader(bulk, target_asset=target)
        signal = trader.signal(lookback=20)

        # Simple execution: act on confidence > 0.4
        if signal["confidence"] > 0.4:
            desired_position = signal["direction"]
        else:
            desired_position = 0

        # Close if position flips or goes flat
        if position != 0 and desired_position != position:
            pnl = position * (current_price - entry_price) * 100000  # 1 lot approx
            balance += pnl
            trades.append({
                "date": current_date,
                "action": "CLOSE",
                "price": current_price,
                "pnl": pnl,
                "balance": balance,
                "signal": signal,
            })
            position = 0
            entry_price = None

        # Open new position
        if position == 0 and desired_position != 0:
            position = desired_position
            entry_price = current_price
            trades.append({
                "date": current_date,
                "action": "OPEN",
                "direction": "LONG" if position > 0 else "SHORT",
                "price": current_price,
                "balance": balance,
                "signal": signal,
            })

    # Close any open position at end
    if position != 0:
        final_price = closes[target].iloc[-1]
        pnl = position * (final_price - entry_price) * 100000
        balance += pnl
        trades.append({
            "date": closes.index[-1],
            "action": "CLOSE_FINAL",
            "price": final_price,
            "pnl": pnl,
            "balance": balance,
            "signal": None,
        })

    trades_df = pd.DataFrame(trades)
    if trades_df.empty:
        print("\nNo trades generated.")
        print("Possible reasons: confidence threshold too high, no ER-bridges, or signals flat.")
        return trades_df, balance

    wins = trades_df[trades_df["action"].str.contains("CLOSE") & (trades_df["pnl"] > 0)]
    losses = trades_df[trades_df["action"].str.contains("CLOSE") & (trades_df["pnl"] <= 0)]
    closes_count = len(trades_df[trades_df["action"].str.contains("CLOSE")])

    print("\n--- HETM Backtest Summary ---")
    print(f"Total trades: {closes_count}")
    print(f"Wins: {len(wins)} | Losses: {len(losses)}")
    print(f"Win rate: {len(wins)/closes_count*100:.1f}%" if closes_count > 0 else "No trades")
    print(f"Final balance: ${balance:,.2f}")
    print(f"Total return: {(balance/100000 - 1)*100:.2f}%")
    print(f"Avg trade PnL: ${trades_df[trades_df['action'].str.contains('CLOSE')]['pnl'].mean():,.2f}" if closes_count > 0 else "")

    trades_df.to_csv(Path(__file__).parent.parent / "data" / "hetm_backtest.csv", index=False)
    return trades_df, balance


if __name__ == "__main__":
    run_backtest()
